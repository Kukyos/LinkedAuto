"""
LinkedIn API service for posting content
"""
import httpx
from typing import Optional, Dict
from app.core.config import settings


class LinkedInService:
    """Service for interacting with LinkedIn API"""
    
    def __init__(self):
        self.base_url = settings.LINKEDIN_API_URL
    
    async def _make_request(self, endpoint: str, access_token: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to LinkedIn API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check rate limit
            if response.status_code == 429:
                raise Exception("LinkedIn API rate limit exceeded")
            
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def get_user_profile(self, access_token: str) -> Dict:
        """Get LinkedIn user profile information"""
        endpoint = "/v2/people/~"
        return await self._make_request(endpoint, access_token)
    
    async def post_content(self, access_token: str, content: str, visibility: str = "PUBLIC") -> str:
        """Post content to LinkedIn"""
        
        # First, get user URN
        profile = await self.get_user_profile(access_token)
        user_urn = profile.get("id")
        
        if not user_urn:
            raise Exception("Could not get user URN from LinkedIn")
        
        # Create post payload
        post_data = {
            "author": f"urn:li:person:{user_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        # Post to LinkedIn
        endpoint = "/v2/ugcPosts"
        response = await self._make_request(endpoint, access_token, "POST", post_data)
        
        # Extract post ID from response
        post_id = response.get("id", "")
        
        # Return the LinkedIn post URL
        return f"https://www.linkedin.com/feed/update/{post_id}/"
    
    async def post_content_with_media(self, access_token: str, content: str, media_url: str, visibility: str = "PUBLIC") -> str:
        """Post content with media to LinkedIn"""
        
        # First, get user URN
        profile = await self.get_user_profile(access_token)
        user_urn = profile.get("id")
        
        if not user_urn:
            raise Exception("Could not get user URN from LinkedIn")
        
        # Register media upload
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{user_urn}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        # This is a simplified version - in production, you'd need to:
        # 1. Register media upload
        # 2. Upload the media file
        # 3. Create post with media reference
        
        # For now, just post text content
        return await self.post_content(access_token, content, visibility)
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh LinkedIn access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.LINKEDIN_CLIENT_ID,
                    "client_secret": settings.LINKEDIN_CLIENT_SECRET
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise Exception("Failed to refresh LinkedIn token")
            
            return response.json()