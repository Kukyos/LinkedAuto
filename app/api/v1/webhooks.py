"""
Webhook handling for GitHub repository events
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
from typing import Dict
from app.core.config import settings
from app.models.database import get_db, Repository, WebhookEvent
from app.services.github_service import GitHubService
from app.services.free_summarization_service import FreeSummarizationService

router = APIRouter()
github_service = GitHubService()
summarization_service = FreeSummarizationService()


def verify_webhook_signature(request_body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle GitHub webhook events"""
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if signature and not verify_webhook_signature(body, signature, settings.WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = request.headers.get("X-GitHub-Event")
    
    # Only process push events
    if event_type != "push":
        return {"status": "ignored", "event": event_type}
    
    # Extract repository info
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name")
    repo_github_id = str(repo_data.get("id", ""))
    
    if not repo_full_name or not repo_github_id:
        raise HTTPException(status_code=400, detail="Missing repository information")
    
    # Find monitored repository
    repo = db.query(Repository).filter(
        Repository.github_repo_id == repo_github_id,
        Repository.is_monitored == True
    ).first()
    
    if not repo:
        return {"status": "ignored", "reason": "repository not monitored"}
    
    # Log webhook event
    webhook_event = WebhookEvent(
        repository_id=repo.id,
        event_type=event_type,
        payload=json.dumps(payload)
    )
    db.add(webhook_event)
    db.commit()
    
    # Check if README was modified
    modified_files = []
    commits = payload.get("commits", [])
    for commit in commits:
        modified_files.extend(commit.get("modified", []))
        modified_files.extend(commit.get("added", []))
    
    readme_modified = any("readme" in file.lower() for file in modified_files)
    
    if not readme_modified:
        return {"status": "processed", "readme_modified": False}
    
    # Check if README contains "Completed"
    try:
        # Get user access token
        user = repo.user
        if not user.github_access_token:
            return {"status": "error", "reason": "no github token"}
        
        from app.core.security import token_encryptor
        access_token = token_encryptor.decrypt_token(user.github_access_token)
        
        # Get README content
        readme_content = await github_service.get_repo_readme(access_token, repo_full_name)
        
        if "Completed" not in readme_content:
            return {"status": "processed", "completed_keyword": False}
        
        # Trigger summarization and posting
        await process_completed_project(db, repo, access_token)
        
        return {"status": "processed", "action": "summarization_triggered"}
        
    except Exception as e:
        # Log error but don't fail the webhook
        print(f"Error processing webhook: {str(e)}")
        return {"status": "error", "error": str(e)}


async def process_completed_project(db: Session, repo: Repository, access_token: str):
    """Process a completed project: summarize and prepare for posting"""
    try:
        # Get repository metadata
        metadata = await github_service.get_repo_metadata(access_token, repo.full_name)
        
        # Generate summary using free summarization service
        summary = await summarization_service.summarize_repository(metadata, "professional")
        
        # Store the summary for user review (in a real implementation, this would be stored in DB)
        # For now, we'll just log it
        print(f"Generated summary for {repo.full_name}: {summary}")
        
        # In production, this would create a LinkedInPost record with status="draft"
        # and notify the user via email/webhook
        
    except Exception as e:
        print(f"Error processing completed project: {str(e)}")
        raise


@router.get("/test")
async def test_webhook():
    """Test endpoint for webhook functionality"""
    return {"status": "webhook endpoint active"}