"""
Repository management routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import httpx
from typing import List, Optional
from app.core.config import settings
from app.core.security import token_encryptor
from app.models.database import get_db, User, Repository
from app.services.github_service import GitHubService

router = APIRouter()
github_service = GitHubService()


@router.get("/list")
async def list_repositories(
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT in real implementation
):
    """List user's GitHub repositories"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.github_access_token:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    try:
        access_token = token_encryptor.decrypt_token(user.github_access_token)
        repos = await github_service.get_user_repos(access_token)
        
        # Get existing monitored repos
        monitored_repo_ids = {r.github_repo_id for r in user.repos if r.is_monitored}
        
        # Mark which ones are already monitored
        for repo in repos:
            repo["is_monitored"] = str(repo["id"]) in monitored_repo_ids
        
        return {"repositories": repos}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch repositories: {str(e)}")


@router.post("/monitor/{repo_id}")
async def monitor_repository(
    repo_id: str,
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Start monitoring a repository"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.github_access_token:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    try:
        access_token = token_encryptor.decrypt_token(user.github_access_token)
        
        # Get repo details from GitHub
        repo_data = await github_service.get_repo_details(access_token, repo_id)
        
        # Check if already exists
        existing_repo = db.query(Repository).filter(
            Repository.user_id == user.id,
            Repository.github_repo_id == repo_id
        ).first()
        
        if existing_repo:
            existing_repo.is_monitored = True
            db.commit()
            return {"message": "Repository monitoring enabled", "repository": existing_repo}
        
        # Create new repository record
        repo = Repository(
            user_id=user.id,
            github_repo_id=repo_id,
            name=repo_data["name"],
            full_name=repo_data["full_name"],
            description=repo_data.get("description"),
            url=repo_data["html_url"],
            is_monitored=True
        )
        
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        # Set up webhook
        webhook_id = await github_service.create_webhook(access_token, repo_data["full_name"])
        if webhook_id:
            repo.webhook_id = webhook_id
            db.commit()
        
        return {"message": "Repository monitoring enabled", "repository": repo}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to monitor repository: {str(e)}")


@router.delete("/monitor/{repo_id}")
async def stop_monitoring_repository(
    repo_id: str,
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Stop monitoring a repository"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repo = db.query(Repository).filter(
        Repository.user_id == user.id,
        Repository.github_repo_id == repo_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Remove webhook if exists
    if repo.webhook_id and user.github_access_token:
        try:
            access_token = token_encryptor.decrypt_token(user.github_access_token)
            await github_service.delete_webhook(access_token, repo.full_name, repo.webhook_id)
        except Exception:
            pass  # Continue even if webhook deletion fails
    
    repo.is_monitored = False
    repo.webhook_id = None
    db.commit()
    
    return {"message": "Repository monitoring disabled"}


@router.get("/monitored")
async def get_monitored_repositories(
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Get user's monitored repositories"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    repos = db.query(Repository).filter(
        Repository.user_id == user.id,
        Repository.is_monitored == True
    ).all()
    
    return {"repositories": repos}