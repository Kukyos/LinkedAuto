# AutoProjectPost Backend

FastAPI backend for AutoProjectPost - Automated GitHub repository monitoring and LinkedIn posting.

## Features

- **FastAPI Framework**: High-performance async web API
- **OAuth Integration**: GitHub and LinkedIn authentication
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Free AI Summarization**: Template-based AI alternative (no OpenAI costs)
- **Webhook Handling**: GitHub webhook processing for real-time updates
- **Security**: JWT authentication with encrypted token storage

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: JWT with OAuth2
- **AI**: Custom template-based summarization (free)
- **Deployment**: Railway (free tier)

## Local Development

### Prerequisites

- Python 3.10+
- PostgreSQL database

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Kukyos/LinkedAuto.git
cd LinkedAuto/backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/autoprojectpost

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-byte-encryption-key

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
```

5. Initialize database:
```bash
python init_db.py
```

6. Run the server:
```bash
uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000

## API Documentation

Once running, visit: http://localhost:8000/docs for interactive API documentation.

## Deployment to Railway

### Prerequisites

1. **GitHub Repository**: Code must be pushed to GitHub
2. **Railway Account**: Sign up at https://railway.app
3. **OAuth Apps**: Configure GitHub and LinkedIn OAuth apps

### Deploy Steps

1. **Connect Repository**:
   - Go to Railway dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Connect your GitHub account and select `LinkedAuto` repository

2. **Environment Variables** (in Railway dashboard → Project Settings → Variables):
   ```
   DATABASE_URL=postgresql://... (auto-provided by Railway)
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   OPENAI_API_KEY=your_openai_api_key (optional - uses free summarization)
   SECRET_KEY=generate_random_32_char_string
   ENCRYPTION_KEY=generate_random_32_char_string
   WEBHOOK_SECRET=generate_random_string
   ALLOWED_ORIGINS=https://your-frontend.vercel.app
   GITHUB_REDIRECT_URI=https://your-project.railway.app/api/v1/auth/github/callback
   LINKEDIN_REDIRECT_URI=https://your-project.railway.app/api/v1/auth/linkedin/callback
   ```

3. **Deploy**: Railway will automatically detect the configuration and deploy

### OAuth Configuration

**GitHub OAuth App** (https://github.com/settings/applications/new):
- Homepage URL: `https://your-frontend.vercel.app`
- Authorization callback URL: `https://your-project.railway.app/api/v1/auth/github/callback`

**LinkedIn OAuth App** (https://www.linkedin.com/developers/apps):
- Authorized redirect URLs: `https://your-project.railway.app/api/v1/auth/linkedin/callback`

## API Endpoints

### Authentication
- `POST /api/v1/auth/github/login` - Get GitHub OAuth URL
- `GET /api/v1/auth/github/callback` - GitHub OAuth callback
- `POST /api/v1/auth/linkedin/login` - Get LinkedIn OAuth URL
- `GET /api/v1/auth/linkedin/callback` - LinkedIn OAuth callback
- `GET /api/v1/auth/me` - Get current user info

### Repositories
- `GET /api/v1/repos/list` - List user repositories
- `POST /api/v1/repos/monitor/{repo_id}` - Start monitoring repository
- `DELETE /api/v1/repos/monitor/{repo_id}` - Stop monitoring repository

### Posts
- `POST /api/v1/posts/summarize/{repo_id}` - Generate post summary
- `POST /api/v1/posts/customize/{post_id}` - Customize post content
- `POST /api/v1/posts/linkedin/{post_id}` - Post to LinkedIn
- `GET /api/v1/posts/user` - Get user posts

### Webhooks
- `POST /api/v1/webhooks/github` - GitHub webhook endpoint

## Database Schema

- **users**: User accounts and OAuth tokens
- **repositories**: Monitored GitHub repositories
- **linkedin_posts**: Generated and posted content
- **webhook_events**: GitHub webhook event logs

## Testing

Run tests:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.