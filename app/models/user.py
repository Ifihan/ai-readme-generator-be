from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    github_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    installation_id = Column(Integer, nullable=True)

    # Relationships
    readme_generations = relationship("ReadmeGeneration", back_populates="user")
    user_preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False
    )


class ReadmeGeneration(Base):
    """README generation history model."""

    __tablename__ = "readme_generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repository_name = Column(String, nullable=False)
    repository_id = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # The generated README content
    # Change this line:
    generation_metadata = Column(
        JSON, nullable=True
    )  # Use generation_metadata instead of metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)  # Track different versions

    # Relationships
    user = relationship("User", back_populates="readme_generations")
    sections = relationship(
        "ReadmeSection",
        back_populates="readme_generation",
        cascade="all, delete-orphan",
    )


class ReadmeSection(Base):
    """README section model to store individual sections of a README."""

    __tablename__ = "readme_sections"

    id = Column(Integer, primary_key=True, index=True)
    readme_generation_id = Column(
        Integer, ForeignKey("readme_generations.id"), nullable=False
    )
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)  # To maintain section order
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    readme_generation = relationship("ReadmeGeneration", back_populates="sections")


class UserPreferences(Base):
    """User preferences for README generation."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    section_preferences = Column(
        JSON, nullable=True
    )  # Store section preferences as JSON
    style_preferences = Column(JSON, nullable=True)  # Store style preferences as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_preferences")
