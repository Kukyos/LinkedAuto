"""
Authentication routes for GitHub and LinkedIn OAuth
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import httpx
from app.core.config import settings
from app.core.security import create_access_token, token_encryptor, get_current_user
from app.models.database import get_db, User
from typing import Optional

router = APIRouter()


@router.get("/github/login")
async def github_login():
    """Initiate GitHub OAuth flow"""
    auth_url = (
        f"{settings.GITHUB_AUTHORIZATION_URL}?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"scope=read:user,user:email,repo"
    )
    return {"auth_url": auth_url}


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback"""
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            settings.GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI
            },
            headers={"Accept": "application/json"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info
        user_response = await client.get(
            f"{settings.GITHUB_API_URL}/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_data = user_response.json()
        
        # Get user email
        email_response = await client.get(
            f"{settings.GITHUB_API_URL}/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        emails = email_response.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), emails[0]["email"])
        
        # Create or update user
        user = db.query(User).filter(User.github_id == str(user_data["id"])).first()
        
        if not user:
            user = User(
                github_id=str(user_data["id"]),
                github_username=user_data["login"],
                email=primary_email,
                github_access_token=token_encryptor.encrypt_token(access_token)
            )
            db.add(user)
        else:
            user.github_access_token = token_encryptor.encrypt_token(access_token)
            user.github_username = user_data["login"]
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id), "github_id": user.github_id})
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "github_username": user.github_username,
                "email": user.email
            }
        }


@router.get("/linkedin/login")
async def linkedin_login():
    """Initiate LinkedIn OAuth flow"""
    auth_url = (
        f"{settings.LINKEDIN_AUTHORIZATION_URL}?"
        f"response_type=code&"
        f"client_id={settings.LINKEDIN_CLIENT_ID}&"
        f"redirect_uri={settings.LINKEDIN_REDIRECT_URI}&"
        f"scope=openid profile email w_member_social"
    )
    return {"auth_url": auth_url}


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str = Query(...),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None)
):
    """Handle LinkedIn OAuth callback"""
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            settings.LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        
        # Get LinkedIn user info
        user_response = await client.get(
            f"{settings.LINKEDIN_API_URL}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        linkedin_data = user_response.json()
        
        # Update existing user or create new one
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            # Try to find user by LinkedIn ID
            user = db.query(User).filter(User.linkedin_id == linkedin_data.get("sub")).first()
            if not user:
                raise HTTPException(status_code=400, detail="Please login with GitHub first")
        
        user.linkedin_id = linkedin_data.get("sub")
        user.linkedin_access_token = token_encryptor.encrypt_token(access_token)
        if refresh_token:
            user.linkedin_refresh_token = token_encryptor.encrypt_token(refresh_token)
        
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "LinkedIn account connected successfully",
            "user": {
                "id": user.id,
                "linkedin_connected": True
            }
        }


@router.get("/me")
async def get_current_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info"""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "github_username": user.github_username,
        "linkedin_connected": user.linkedin_id is not None,
        "posts_count": len(user.posts) if user.posts else 0
    }
