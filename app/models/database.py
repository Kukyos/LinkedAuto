"""
Database models and session management
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.core.config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    github_id = Column(String, unique=True, index=True)
    github_username = Column(String)
    github_access_token = Column(Text)  # Encrypted
    linkedin_id = Column(String, unique=True, nullable=True)
    linkedin_access_token = Column(Text, nullable=True)  # Encrypted
    linkedin_refresh_token = Column(Text, nullable=True)  # Encrypted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    repos = relationship("Repository", back_populates="user")
    posts = relationship("LinkedInPost", back_populates="user")


class Repository(Base):
    """GitHub repository model"""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    github_repo_id = Column(String, unique=True, index=True)
    name = Column(String)
    full_name = Column(String)
    description = Column(Text, nullable=True)
    url = Column(String)
    is_monitored = Column(Boolean, default=False)
    webhook_id = Column(String, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="repos")
    posts = relationship("LinkedInPost", back_populates="repository")


class LinkedInPost(Base):
    """LinkedIn post model"""
    __tablename__ = "linkedin_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    content = Column(Text)
    tone = Column(String)  # professional, playful, technical, cocky
    linkedin_post_id = Column(String, nullable=True)
    status = Column(String)  # draft, posted, failed
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="posts")
    repository = relationship("Repository", back_populates="posts")


class WebhookEvent(Base):
    """Webhook event log"""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    event_type = Column(String)
    payload = Column(Text)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
