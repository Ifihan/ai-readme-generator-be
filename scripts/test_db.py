#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal, engine
from app.models.user import User, ReadmeGeneration
from app.db import create_user, get_user_by_username, get_user_readme_generations


def test_connection():
    """Test database connection and perform basic CRUD operations."""
    print("Testing database connection...")

    try:
        # Create a test session
        db = SessionLocal()

        # Check if we can query the database
        try:
            users = db.query(User).limit(5).all()
            print(f"Successfully connected to database. Found {len(users)} users.")
        except Exception as e:
            print(f"Error querying database: {e}")
            return False

        # Test create operation
        test_user = {
            "username": f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "github_id": "12345",
            "email": "test@example.com",
            "avatar_url": "https://example.com/avatar.png",
            "installation_id": 67890,
        }

        try:
            created_user = create_user(db, test_user)
            print(f"Created test user with ID: {created_user.id}")

            # Test read operation
            fetched_user = get_user_by_username(db, test_user["username"])
            if fetched_user:
                print(f"Successfully retrieved user: {fetched_user.username}")
            else:
                print("Failed to retrieve created user")
                return False

            # Test readme generation creation
            readme_data = {
                "user_id": created_user.id,
                "repository_name": "test/repo",
                "repository_id": "98765",
                "content": "# Test README\n\nThis is a test README.",
                "metadata": {"test": True},
            }

            test_generation = ReadmeGeneration(**readme_data)
            db.add(test_generation)
            db.commit()
            db.refresh(test_generation)
            print(f"Created test README generation with ID: {test_generation.id}")

            # Test retrieval of readme generations
            generations = get_user_readme_generations(db, created_user.id)
            print(f"Retrieved {len(generations)} README generations for user")

            # Clean up test data
            db.delete(test_generation)
            db.delete(created_user)
            db.commit()
            print("Cleaned up test data")

            return True

        except Exception as e:
            print(f"Error during CRUD operations: {e}")
            return False

    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_connection()
    if success:
        print("Database test completed successfully.")
        sys.exit(0)
    else:
        print("Database test failed.")
        sys.exit(1)
