"""
Posts management routes: summarization and LinkedIn posting
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
import httpx
from typing import Optional, Dict
from app.core.config import settings
from app.core.security import token_encryptor
from app.models.database import get_db, User, Repository, LinkedInPost
from app.services.github_service import GitHubService
from app.services.free_summarization_service import FreeSummarizationService
from app.services.linkedin_service import LinkedInService

router = APIRouter()
github_service = GitHubService()
summarization_service = FreeSummarizationService()
linkedin_service = LinkedInService()


@router.post("/summarize/{repo_id}")
async def summarize_repository(
    repo_id: str,
    tone: str = Query("professional", description="Post tone: professional, playful, technical, cocky"),
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Generate a LinkedIn post summary for a repository"""
    
    # Find repository
    repo = db.query(Repository).filter(
        Repository.github_repo_id == repo_id,
        Repository.user_id == user_id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get user and check GitHub access
    user = db.query(User).filter(User.id == user_id).first()
    if not user.github_access_token:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    try:
        # Get repository metadata
        access_token = token_encryptor.decrypt_token(user.github_access_token)
        metadata = await github_service.get_repo_metadata(access_token, repo.full_name)
        
        # Generate summary
        summary = await summarization_service.summarize_repository(metadata, tone)
        
        # Create LinkedIn post record
        linkedin_post = LinkedInPost(
            user_id=user_id,
            repository_id=repo.id,
            content=summary,
            tone=tone,
            status="draft"
        )
        
        db.add(linkedin_post)
        db.commit()
        db.refresh(linkedin_post)
        
        return {
            "post_id": linkedin_post.id,
            "summary": summary,
            "tone": tone,
            "status": "draft",
            "repository": {
                "name": repo.name,
                "url": repo.url
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to summarize repository: {str(e)}")


@router.put("/customize/{post_id}")
async def customize_post(
    post_id: int,
    tone: str = Query("professional"),
    custom_instructions: str = Query("", description="Additional customization instructions"),
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Customize an existing post"""
    
    # Find post
    post = db.query(LinkedInPost).filter(
        LinkedInPost.id == post_id,
        LinkedInPost.user_id == user_id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    try:
        # Customize post
        customized_content = await summarization_service.customize_post(
            post.content, tone, custom_instructions
        )
        
        # Update post
        post.content = customized_content
        post.tone = tone
        db.commit()
        
        return {
            "post_id": post.id,
            "content": customized_content,
            "tone": tone,
            "status": post.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to customize post: {str(e)}")


@router.post("/linkedin/{post_id}")
async def post_to_linkedin(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Post to LinkedIn"""
    
    # Find post
    post = db.query(LinkedInPost).filter(
        LinkedInPost.id == post_id,
        LinkedInPost.user_id == user_id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check LinkedIn connection
    user = db.query(User).filter(User.id == user_id).first()
    if not user.linkedin_access_token:
        raise HTTPException(status_code=400, detail="LinkedIn not connected")
    
    # Update status to posting
    post.status = "posting"
    db.commit()
    
    # Post in background
    background_tasks.add_task(
        post_to_linkedin_background,
        post_id,
        user.linkedin_access_token,
        db
    )
    
    return {
        "post_id": post.id,
        "status": "posting",
        "message": "Post is being published to LinkedIn"
    }


async def post_to_linkedin_background(post_id: int, encrypted_token: str, db: Session):
    """Background task to post to LinkedIn"""
    try:
        # Get post
        post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()
        if not post:
            return
        
        # Decrypt token
        access_token = token_encryptor.decrypt_token(encrypted_token)
        
        # Post to LinkedIn
        post_url = await linkedin_service.post_content(access_token, post.content)
        
        # Update post status
        post.status = "posted"
        post.linkedin_post_id = post_url
        from datetime import datetime
        post.posted_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Update status to failed
        post.status = "failed"
        db.commit()
        print(f"Failed to post to LinkedIn: {str(e)}")


@router.get("/user")
async def get_user_posts(
    db: Session = Depends(get_db),
    user_id: int = Query(...)  # Would come from JWT
):
    """Get user's posts"""
    
    posts = db.query(LinkedInPost).filter(
        LinkedInPost.user_id == user_id
    ).order_by(LinkedInPost.created_at.desc()).all()
    
    return {
        "posts": [
            {
                "id": post.id,
                "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "tone": post.tone,
                "status": post.status,
                "posted_at": post.posted_at,
                "repository": {
                    "name": post.repository.name,
                    "url": post.repository.url
                } if post.repository else None
            }
            for post in posts
        ]
    }


@router.get("/tones")
async def get_available_tones():
    """Get available post tones"""
    return {
        "tones": summarization_service.get_tone_templates()
    }