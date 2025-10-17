"""
OpenAI service for repository summarization
"""
import openai
from typing import Dict, List
from app.core.config import settings


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
    
    async def summarize_repository(self, repo_metadata: Dict, tone: str = "professional") -> str:
        """Generate a LinkedIn post summary for a repository"""
        
        # Extract key information
        name = repo_metadata.get("name", "")
        description = repo_metadata.get("description", "")
        languages = repo_metadata.get("languages", {})
        commits = repo_metadata.get("commits", [])
        readme = repo_metadata.get("readme", "")
        contributors = repo_metadata.get("contributors", [])
        
        # Format languages
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        languages_str = ", ".join([lang for lang, _ in top_languages])
        
        # Format recent commits
        commit_messages = []
        for commit in commits[:5]:  # Last 5 commits
            message = commit.get("message", "").split("\n")[0]  # First line only
            if message and len(message) > 10:  # Filter out trivial commits
                commit_messages.append(message[:100])  # Truncate long messages
        
        commits_str = "; ".join(commit_messages[:3])  # Top 3 meaningful commits
        
        # Create prompt
        prompt = f"""
Summarize this GitHub repository for a LinkedIn post.
Input:
- Repo name: {name}
- Description: {description}
- Languages: {languages_str}
- Recent commits: {commits_str}
- README excerpt: {readme[:1000]}...

Output:
1. Concise project summary (2 sentences)
2. Key technologies
3. What makes it unique
4. One closing sentence fit for LinkedIn tone "{tone}"
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical writer creating engaging LinkedIn posts about software projects."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    def get_tone_templates(self) -> Dict[str, str]:
        """Get available tone templates"""
        return {
            "professional": "Excited to share this completed project with the community!",
            "playful": "Just wrapped up this fun project - check it out! 🚀",
            "technical": "Completed implementation featuring advanced patterns and best practices.",
            "cocky": "Crushed this project - the code doesn't get any cleaner than this! 💪"
        }
    
    async def customize_post(self, base_summary: str, tone: str, custom_instructions: str = "") -> str:
        """Customize a post with specific tone and instructions"""
        
        prompt = f"""
Take this repository summary and rewrite it as a LinkedIn post with "{tone}" tone.

Original summary:
{base_summary}

Additional instructions: {custom_instructions}

Make it engaging, professional, and suitable for LinkedIn. Include relevant hashtags and emojis where appropriate.
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a social media content creator specializing in technical posts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.8
            )
            
            customized_post = response.choices[0].message.content.strip()
            return customized_post
            
        except Exception as e:
            raise Exception(f"Failed to customize post: {str(e)}")