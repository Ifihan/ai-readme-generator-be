import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.base import Base, engine
from app.config import settings


async def init_db():
    """Initialize the database by creating all tables."""
    print(f"Initializing database at {settings.DATABASE_URL}")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())
