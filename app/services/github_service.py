"""
GitHub API service for repository operations and webhooks
"""
import httpx
from typing import List, Dict, Optional
from app.core.config import settings


class GitHubService:
    """Service for interacting with GitHub API"""
    
    def __init__(self):
        self.base_url = settings.GITHUB_API_URL
        self.rate_limit_remaining = settings.GITHUB_API_RATE_LIMIT
    
    async def _make_request(self, endpoint: str, access_token: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to GitHub API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutoProjectPost/1.0"
        }
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check rate limit
            if response.status_code == 403 and "rate limit" in response.text.lower():
                raise Exception("GitHub API rate limit exceeded")
            
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def get_user_repos(self, access_token: str) -> List[Dict]:
        """Get user's repositories"""
        repos = []
        page = 1
        
        while True:
            endpoint = f"/user/repos?page={page}&per_page=100&sort=updated&affiliation=owner"
            page_repos = await self._make_request(endpoint, access_token)
            
            if not page_repos:
                break
                
            repos.extend(page_repos)
            page += 1
            
            # Limit to prevent excessive API calls
            if len(repos) >= 1000:
                break
        
        # Format repositories
        formatted_repos = []
        for repo in repos:
            formatted_repos.append({
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description"),
                "url": repo["html_url"],
                "private": repo["private"],
                "language": repo.get("language"),
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "updated_at": repo["updated_at"]
            })
        
        return formatted_repos
    
    async def get_repo_details(self, access_token: str, repo_id: str) -> Dict:
        """Get detailed repository information"""
        endpoint = f"/repositories/{repo_id}"
        return await self._make_request(endpoint, access_token)
    
    async def get_repo_readme(self, access_token: str, full_name: str) -> str:
        """Get repository README content"""
        endpoint = f"/repos/{full_name}/readme"
        try:
            response = await self._make_request(endpoint, access_token)
            import base64
            return base64.b64decode(response["content"]).decode("utf-8")
        except Exception:
            return ""
    
    async def get_repo_languages(self, access_token: str, full_name: str) -> Dict:
        """Get repository language statistics"""
        endpoint = f"/repos/{full_name}/languages"
        return await self._make_request(endpoint, access_token)
    
    async def get_repo_commits(self, access_token: str, full_name: str, limit: int = 10) -> List[Dict]:
        """Get recent commits"""
        endpoint = f"/repos/{full_name}/commits?per_page={limit}"
        commits = await self._make_request(endpoint, access_token)
        
        formatted_commits = []
        for commit in commits:
            formatted_commits.append({
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"]
            })
        
        return formatted_commits
    
    async def get_repo_contributors(self, access_token: str, full_name: str) -> List[Dict]:
        """Get repository contributors"""
        endpoint = f"/repos/{full_name}/contributors"
        contributors = await self._make_request(endpoint, access_token)
        
        formatted_contributors = []
        for contributor in contributors[:10]:  # Limit to top 10
            formatted_contributors.append({
                "login": contributor["login"],
                "contributions": contributor["contributions"],
                "avatar_url": contributor["avatar_url"]
            })
        
        return formatted_contributors
    
    async def create_webhook(self, access_token: str, full_name: str) -> Optional[str]:
        """Create webhook for repository"""
        endpoint = f"/repos/{full_name}/hooks"
        webhook_config = {
            "name": "web",
            "active": True,
            "events": ["push", "pull_request"],
            "config": {
                "url": f"{settings.GITHUB_REDIRECT_URI.replace('/auth/github/callback', '/webhooks/github')}",
                "content_type": "json",
                "secret": settings.WEBHOOK_SECRET
            }
        }
        
        try:
            response = await self._make_request(endpoint, access_token, "POST", webhook_config)
            return str(response["id"])
        except Exception:
            return None
    
    async def delete_webhook(self, access_token: str, full_name: str, webhook_id: str):
        """Delete webhook from repository"""
        endpoint = f"/repos/{full_name}/hooks/{webhook_id}"
        await self._make_request(endpoint, access_token, "DELETE")
    
    async def get_repo_metadata(self, access_token: str, full_name: str) -> Dict:
        """Get comprehensive repository metadata for summarization"""
        try:
            # Get basic repo info
            repo_info = await self.get_repo_details(access_token, full_name.split("/")[1])
            
            # Get additional data
            readme = await self.get_repo_readme(access_token, full_name)
            languages = await self.get_repo_languages(access_token, full_name)
            commits = await self.get_repo_commits(access_token, full_name)
            contributors = await self.get_repo_contributors(access_token, full_name)
            
            return {
                "name": repo_info["name"],
                "full_name": repo_info["full_name"],
                "description": repo_info.get("description", ""),
                "url": repo_info["html_url"],
                "language": repo_info.get("language"),
                "languages": languages,
                "stars": repo_info["stargazers_count"],
                "forks": repo_info["forks_count"],
                "readme": readme,
                "commits": commits,
                "contributors": contributors
            }
        except Exception as e:
            raise Exception(f"Failed to get repo metadata: {str(e)}")