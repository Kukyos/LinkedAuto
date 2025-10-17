"""
Backend unit tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.models.database import init_db, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependencies
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    # Create test database
    init_db()
    yield
    # Clean up
    os.remove("./test.db")

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "AutoProjectPost" in response.json()["service"]

def test_github_login_redirect():
    """Test GitHub OAuth login redirect"""
    response = client.get("/api/v1/auth/github/login")
    assert response.status_code == 200
    assert "auth_url" in response.json()
    assert "github.com/login/oauth/authorize" in response.json()["auth_url"]

def test_linkedin_login_redirect():
    """Test LinkedIn OAuth login redirect"""
    response = client.get("/api/v1/auth/linkedin/login")
    assert response.status_code == 200
    assert "auth_url" in response.json()
    assert "linkedin.com/oauth/v2/authorization" in response.json()["auth_url"]

def test_get_available_tones():
    """Test getting available post tones"""
    response = client.get("/api/v1/posts/tones")
    assert response.status_code == 200
    tones = response.json()["tones"]
    assert "professional" in tones
    assert "playful" in tones
    assert "technical" in tones
    assert "cocky" in tones