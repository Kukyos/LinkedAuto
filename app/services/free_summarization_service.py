"""
Free summarization service using templates and rules (no external API costs)
"""
from typing import Dict, List
import re
import random


class FreeSummarizationService:
    """Free alternative to AI summarization using templates and rules"""

    def __init__(self):
        self.templates = {
            "professional": [
                "Excited to share that I've completed {name}, a {description}. Built with {languages}, this project demonstrates {unique_features}. Check it out on GitHub! #softwaredevelopment #opensource",
                "Proud to announce the completion of {name}, {description}. Leveraging {languages} and featuring {unique_features}, this project showcases modern development practices. #coding #technology",
                "Just finished {name}, {description}. The project utilizes {languages} and includes {unique_features}. Grateful for the learning experience and excited to share with the community! #programming #github"
            ],
            "playful": [
                "🎉 Just wrapped up {name} - {description}! Built with {languages} and packed with {unique_features}. Who knew coding could be this fun? Check it out! 🚀 #codinglife #github",
                "Boom! {name} is complete! {description} featuring {languages} and some cool {unique_features}. Time to celebrate with some code! 🎊 #programming #opensource",
                "Mission accomplished! 🚀 {name} is ready for action. {description} with {languages} and awesome {unique_features}. Can't wait to see what you build with it! #developerlife"
            ],
            "technical": [
                "Completed implementation of {name}: {description}. Architecture leverages {languages} with focus on {unique_features}. Repository available for review and contribution. #softwareengineering #systemdesign",
                "Successfully delivered {name}, {description}. Technical stack: {languages}. Key features include {unique_features}. Code quality maintained through comprehensive testing and documentation. #engineering #devops",
                "{name} implementation complete. {description} utilizing {languages} and implementing {unique_features}. Project demonstrates adherence to software engineering best practices. #architecture #development"
            ],
            "cocky": [
                "Crushed it! 💪 {name} is complete and it's a masterpiece. {description} built with {languages} and featuring {unique_features}. The code doesn't get any cleaner than this! #codingchamp #github",
                "Nailed it! 🎯 {name} is finished and it's pure gold. {description} with {languages} and killer {unique_features}. This project is next-level! 🔥 #codeboss #development",
                "Destroyed the competition! 🏆 {name} is done and it's legendary. {description} featuring {languages} and epic {unique_features}. Bow down to this code! 👑 #programminggod #opensource"
            ]
        }

    async def summarize_repository(self, repo_metadata: Dict, tone: str = "professional") -> str:
        """Generate a LinkedIn post summary for a repository using templates"""

        # Extract key information
        name = repo_metadata.get("name", "my project")
        description = repo_metadata.get("description", "an awesome software project")
        languages = repo_metadata.get("languages", {})
        commits = repo_metadata.get("commits", [])
        readme = repo_metadata.get("readme", "")

        # Format languages
        if languages:
            top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]
            languages_str = ", ".join([lang for lang, _ in top_languages])
        else:
            languages_str = "modern technologies"

        # Extract unique features from README and commits
        unique_features = self._extract_features(readme, commits)

        # Select random template for variety
        template_list = self.templates.get(tone, self.templates["professional"])
        template = random.choice(template_list)

        # Fill in the template
        summary = template.format(
            name=name,
            description=description,
            languages=languages_str,
            unique_features=unique_features
        )

        return summary

    def _extract_features(self, readme: str, commits: List[Dict]) -> str:
        """Extract unique features from README and commit messages"""
        features = []

        # Look for common feature indicators in README
        readme_lower = readme.lower()

        feature_keywords = {
            "api": "RESTful API design",
            "database": "robust data management",
            "authentication": "secure authentication",
            "testing": "comprehensive testing",
            "docker": "containerization",
            "ci/cd": "automated deployment",
            "react": "modern React architecture",
            "typescript": "type-safe development",
            "microservice": "microservices architecture",
            "machine learning": "AI/ML capabilities",
            "security": "advanced security features",
            "performance": "high-performance optimization",
            "scalability": "scalable architecture",
            "ui/ux": "intuitive user interface"
        }

        for keyword, feature in feature_keywords.items():
            if keyword in readme_lower:
                features.append(feature)

        # Extract features from commit messages
        commit_features = []
        for commit in commits[:10]:  # Check last 10 commits
            message = commit.get("message", "").lower()
            if "add" in message and ("feature" in message or "functionality" in message):
                commit_features.append("new functionality")
            elif "implement" in message:
                commit_features.append("advanced implementation")
            elif "optimize" in message or "performance" in message:
                commit_features.append("performance optimization")
            elif "security" in message:
                commit_features.append("security enhancements")

        # Combine and deduplicate
        all_features = list(set(features + commit_features))

        if all_features:
            return ", ".join(all_features[:3])  # Limit to 3 features
        else:
            # Default features if nothing specific found
            default_features = [
                "clean code architecture",
                "modern development practices",
                "comprehensive documentation"
            ]
            return ", ".join(random.sample(default_features, 2))

    def get_tone_templates(self) -> Dict[str, str]:
        """Get available tone templates"""
        return {
            "professional": "Excited to share this completed project with the community!",
            "playful": "Just wrapped up this fun project - check it out! 🚀",
            "technical": "Completed implementation featuring advanced patterns and best practices.",
            "cocky": "Crushed this project - the code doesn't get any cleaner than this! 💪"
        }

    async def customize_post(self, base_summary: str, tone: str, custom_instructions: str = "") -> str:
        """Customize a post with specific tone and instructions (basic version)"""
        # For the free version, we'll just return the base summary
        # In a more advanced free version, we could use NLTK or spaCy for text processing
        # But for now, keep it simple

        if custom_instructions:
            # Basic customization based on keywords
            custom_instructions_lower = custom_instructions.lower()

            if "more technical" in custom_instructions_lower:
                base_summary += "\n\n#TechnicalDetails #SoftwareEngineering"
            elif "more casual" in custom_instructions_lower:
                base_summary = base_summary.replace("Excited to share", "Hey everyone, check out")
            elif "add hashtags" in custom_instructions_lower:
                base_summary += "\n\n#Programming #GitHub #OpenSource"

        return base_summary