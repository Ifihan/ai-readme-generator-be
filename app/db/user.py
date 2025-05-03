from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.user import User, ReadmeGeneration, ReadmeSection, UserPreferences


# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_github_id(db: Session, github_id: str) -> Optional[User]:
    """Get user by GitHub ID."""
    return db.query(User).filter(User.github_id == github_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users."""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    """Create a new user."""
    db_user = User(**user_data)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise
    return db_user


def update_user(db: Session, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
    """Update a user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    for key, value in user_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_by_username(
    db: Session, username: str, user_data: Dict[str, Any]
) -> Optional[User]:
    """Update a user by username."""
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None

    for key, value in user_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True


# README Generation CRUD operations
def create_readme_generation(
    db: Session, readme_data: Dict[str, Any]
) -> ReadmeGeneration:
    """Create a new README generation record."""
    db_generation = ReadmeGeneration(**readme_data)
    db.add(db_generation)
    db.commit()
    db.refresh(db_generation)
    return db_generation


def get_readme_generation(
    db: Session, generation_id: int
) -> Optional[ReadmeGeneration]:
    """Get a README generation by ID."""
    return (
        db.query(ReadmeGeneration).filter(ReadmeGeneration.id == generation_id).first()
    )


def get_user_readme_generations(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[ReadmeGeneration]:
    """Get all README generations for a user."""
    return (
        db.query(ReadmeGeneration)
        .filter(ReadmeGeneration.user_id == user_id)
        .order_by(ReadmeGeneration.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_repository_readme_generations(
    db: Session, user_id: int, repository_id: str
) -> List[ReadmeGeneration]:
    """Get all README generations for a specific repository."""
    return (
        db.query(ReadmeGeneration)
        .filter(
            ReadmeGeneration.user_id == user_id,
            ReadmeGeneration.repository_id == repository_id,
        )
        .order_by(ReadmeGeneration.created_at.desc())
        .all()
    )


def create_new_readme_version(
    db: Session, previous_generation_id: int, content: str, metadata: Dict = None
) -> ReadmeGeneration:
    """Create a new version based on an existing README generation."""
    prev_generation = get_readme_generation(db, previous_generation_id)
    if not prev_generation:
        raise ValueError(
            f"README generation with ID {previous_generation_id} not found"
        )

    # Create new version with incremented version number
    new_version = ReadmeGeneration(
        user_id=prev_generation.user_id,
        repository_name=prev_generation.repository_name,
        repository_id=prev_generation.repository_id,
        content=content,
        metadata=metadata or prev_generation.metadata,
        version=prev_generation.version + 1,
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


# README Section CRUD operations
def create_readme_section(db: Session, section_data: Dict[str, Any]) -> ReadmeSection:
    """Create a new README section."""
    db_section = ReadmeSection(**section_data)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


def get_readme_sections(db: Session, readme_generation_id: int) -> List[ReadmeSection]:
    """Get all sections for a README generation."""
    return (
        db.query(ReadmeSection)
        .filter(ReadmeSection.readme_generation_id == readme_generation_id)
        .order_by(ReadmeSection.order)
        .all()
    )


def update_readme_section(
    db: Session, section_id: int, section_data: Dict[str, Any]
) -> Optional[ReadmeSection]:
    """Update a README section."""
    db_section = db.query(ReadmeSection).filter(ReadmeSection.id == section_id).first()
    if not db_section:
        return None

    for key, value in section_data.items():
        setattr(db_section, key, value)

    db_section.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_section)
    return db_section


# User Preferences CRUD operations
def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreferences]:
    """Get user preferences."""
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()


def create_or_update_user_preferences(
    db: Session, user_id: int, preferences_data: Dict[str, Any]
) -> UserPreferences:
    """Create or update user preferences."""
    db_preferences = get_user_preferences(db, user_id)

    if db_preferences:
        # Update existing preferences
        for key, value in preferences_data.items():
            setattr(db_preferences, key, value)

        db_preferences.updated_at = datetime.utcnow()
    else:
        # Create new preferences
        db_preferences = UserPreferences(user_id=user_id, **preferences_data)
        db.add(db_preferences)

    db.commit()
    db.refresh(db_preferences)
    return db_preferences
