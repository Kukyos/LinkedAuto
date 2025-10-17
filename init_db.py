#!/usr/bin/env python3
"""
Database initialization script for AutoProjectPost
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.models.database import init_db, engine, Base
from app.core.config import settings

def main():
    """Initialize the database"""
    print("🚀 Initializing AutoProjectPost database...")

    try:
        # Create all tables
        print("📋 Creating database tables...")
        init_db()

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        print(f"✅ Created {len(tables)} tables: {', '.join(tables)}")

        print("🎉 Database initialization completed successfully!")
        print(f"📍 Database location: {settings.DATABASE_URL}")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()