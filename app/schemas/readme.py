from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ReadmeSection(BaseModel):
    """Model for a section in the README file."""

    name: str = Field(..., description="Name of the section")
    description: str = Field(
        ..., description="Description of what this section should contain"
    )
    required: bool = Field(
        default=False, description="Whether this section is required"
    )
    order: int = Field(
        default=0, description="Order in which this section shuold appear"
    )

    class Config:
        json_json_schema_extra = {
            "example": {
                "name": "Installation",
                "description": "Instructions for installing the project",
                "required": True,
                "order": 2,
            }
        }


class ReadmeGenerationRequest(BaseModel):
    """Model for a README generation request."""

    repository_url: str = Field(
        ..., description="URL or owner/name of the GitHub Respository"
    )
    sections: List[ReadmeSection] = Field(
        ..., description="List of sections to include in the README"
    )
    include_badges: bool = Field(
        default=True, description="Whether to include badges in the README"
    )
    badge_style: Optional[str] = Field(
        default="flat",
        description="Style for badges (flat, flat-square, plastic, etc.)",
    )

    class Config:
        json_json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/username/project",
                "sections": [
                    {
                        "name": "Introduction",
                        "description": "Brief introduction to the project",
                        "required": True,
                        "order": 1,
                    },
                    {
                        "name": "Installation",
                        "description": "Instructions for installing the project",
                        "required": True,
                        "order": 2,
                    },
                ],
                "include_badges": True,
                "badge_style": "flat",
            }
        }


class ReadmeResponse(BaseModel):
    """Model for a README generation response."""
    
    entry_id: Optional[str] = Field(default=None, description="Generated README content in Markdown format")
    content: str = Field(..., description="Generated README content in Markdown format")
    sections_generated: List[str] = Field(
        ..., description="List of sections that were requested to be generated"
    )

    class Config:
        json_json_schema_extra = {
            "example": {
                "content": "# Project Name\n\n## Introduction\n\nThis is a brief introduction...",
                "sections_generated": ["Introduction", "Installation"],
            }
        }


class ReadmeRefineRequest(BaseModel):
    """Model for refining an existing README."""

    content: str = Field(..., description="Current README content")
    feedback: str = Field(..., description="User feedback for refinement")

    class Config:
        json_json_schema_extra = {
            "example": {
                "content": "# Project Name\n\n## Introduction\n\nThis is a brief introduction...",
                "feedback": "Please make the installation instructions more detailed.",
            }
        }


class ReadmeSaveRequest(BaseModel):
    """Model for saving a README to GitHub."""

    repository_url: str = Field(
        ..., description="URL or owner/name of the GitHub repository"
    )
    content: str = Field(..., description="README content to save")
    path: str = Field(default="README.md", description="Path to save the README file")
    commit_message: str = Field(
        ..., description="Commit message for the README update"
    )
    branch: Optional[str] = Field(
        default=None,
        description="Branch to save to (default: repository default branch)",
    )

    class Config:
        json_json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/username/project",
                "content": "# Project Name\n\n## Introduction\n\nThis is a brief introduction...",
                "path": "README.md",
                "commit_message": "Update README with new sections",
                "branch": "main",
            }
        }


class SectionTemplate(BaseModel):
    """Model for a predefined README section template."""

    id: str = Field(..., description="Unique identifier for the section template")
    name: str = Field(..., description="Name of the section")
    description: str = Field(
        ..., description="Description of what this section contains"
    )
    is_default: bool = Field(
        default=False, description="Whether this section is included by default"
    )
    order: int = Field(..., description="Default order for this section")

    class Config:
        json_json_schema_extra = {
            "example": {
                "id": "installation",
                "name": "Installation",
                "description": "Instructions for installing the project",
                "is_default": True,
                "order": 2,
            }
        }


# Common section templates that can be offered to users
DEFAULT_SECTION_TEMPLATES = [
    SectionTemplate(
        id="introduction",
        name="Introduction",
        description="Brief overview explaining what the project does, the problem it solves, and its key benefits",
        is_default=True,
        order=1,
    ),
    SectionTemplate(
        id="table_of_contents",
        name="Table of Contents",
        description="Navigational links to all major sections in the README",
        is_default=True,
        order=2,
    ),
    SectionTemplate(
        id="features",
        name="Features",
        description="Comprehensive list of the project's key features and capabilities",
        is_default=True,
        order=3,
    ),
    SectionTemplate(
        id="tech_stack",
        name="Tech Stack",
        description="Technologies, frameworks, and libraries used in the project",
        is_default=True,
        order=4,
    ),
    SectionTemplate(
        id="prerequisites",
        name="Prerequisites",
        description="System requirements and dependencies needed before installation",
        is_default=True,
        order=5,
    ),
    SectionTemplate(
        id="installation",
        name="Installation",
        description="Step-by-step instructions for setting up and installing the project locally",
        is_default=True,
        order=6,
    ),
    SectionTemplate(
        id="configuration",
        name="Configuration",
        description="Environment variables, configuration files, and setup options",
        is_default=False,
        order=7,
    ),
    SectionTemplate(
        id="usage",
        name="Usage",
        description="Code examples and instructions showing how to use the project",
        is_default=True,
        order=8,
    ),
    SectionTemplate(
        id="api_reference",
        name="API Reference",
        description="API endpoints, methods, parameters, and responses documentation",
        is_default=False,
        order=9,
    ),
    SectionTemplate(
        id="project_structure",
        name="Project Structure",
        description="Overview of the codebase organization, key directories, and files",
        is_default=False,
        order=10,
    ),
    SectionTemplate(
        id="testing",
        name="Testing",
        description="Instructions for running tests and understanding test coverage",
        is_default=False,
        order=11,
    ),
    SectionTemplate(
        id="deployment",
        name="Deployment",
        description="Steps and requirements for deploying the project to production",
        is_default=False,
        order=12,
    ),
    SectionTemplate(
        id="contributing",
        name="Contributing",
        description="Guidelines and workflow for contributing code, reporting issues, and submitting pull requests",
        is_default=True,
        order=13,
    ),
    SectionTemplate(
        id="license",
        name="License",
        description="Project licensing information and usage terms",
        is_default=True,
        order=14,
    ),
]


class ReadmeHistoryEntry(BaseModel):
    """Model for a README history entry."""
    
    id: Optional[str] = Field(None, description="Unique identifier for the history entry")
    username: str = Field(..., description="Username of the user who generated the README")
    repository_url: str = Field(..., description="Repository URL for which README was generated")
    repository_name: str = Field(..., description="Repository name for display")
    content: str = Field(..., description="Generated README content")
    sections_generated: List[str] = Field(..., description="List of sections that were generated")
    generation_type: str = Field(..., description="Type of generation (new, improved, refined)")
    created_at: datetime = Field(..., description="When the README was generated")
    file_size: int = Field(..., description="Size of the README content in bytes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "64f8b2a1c9e1234567890abc",
                "username": "john_doe",
                "repository_url": "https://github.com/john/awesome-project",
                "repository_name": "awesome-project",
                "content": "# Awesome Project\n\n## Introduction\n\nThis is an awesome project...",
                "sections_generated": ["Introduction", "Installation", "Usage"],
                "generation_type": "new",
                "created_at": "2024-01-15T10:30:00Z",
                "file_size": 1024
            }
        }


class ReadmeHistoryResponse(BaseModel):
    """Model for README history list response."""
    
    entries: List[ReadmeHistoryEntry] = Field(..., description="List of README history entries")
    total_count: int = Field(..., description="Total number of history entries for the user")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of entries per page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entries": [
                    {
                        "id": "64f8b2a1c9e1234567890abc",
                        "username": "john_doe",
                        "repository_url": "https://github.com/john/awesome-project",
                        "repository_name": "awesome-project",
                        "sections_generated": ["Introduction", "Installation"],
                        "generation_type": "new",
                        "created_at": "2024-01-15T10:30:00Z",
                        "file_size": 1024
                    }
                ],
                "total_count": 5,
                "page": 1,
                "page_size": 10
            }
        }


class FeedbackRating(str, Enum):
    """Enum for feedback ratings."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    TERRIBLE = "terrible"


class FeedbackCreateRequest(BaseModel):
    """Model for creating feedback on a README generation."""
    
    readme_history_id: str = Field(..., description="ID of the README history entry")
    rating: FeedbackRating = Field(..., description="Overall rating of the generated README")
    helpful_sections: Optional[List[str]] = Field(default=[], description="Sections that were helpful")
    problematic_sections: Optional[List[str]] = Field(default=[], description="Sections that had issues")
    general_comments: Optional[str] = Field(default="", description="General feedback comments")
    suggestions: Optional[str] = Field(default="", description="Suggestions for improvement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "readme_history_id": "64f8b2a1c9e1234567890abc",
                "rating": "good",
                "helpful_sections": ["Introduction", "Installation"],
                "problematic_sections": ["Usage"],
                "general_comments": "Overall good README but usage examples could be clearer",
                "suggestions": "Add more code examples in the Usage section"
            }
        }


class FeedbackResponse(BaseModel):
    """Model for feedback response."""
    
    id: str = Field(..., description="Unique identifier for the feedback")
    username: str = Field(..., description="Username of the user who provided feedback")
    readme_history_id: str = Field(..., description="ID of the README history entry")
    repository_name: str = Field(..., description="Repository name for display")
    rating: FeedbackRating = Field(..., description="Overall rating of the generated README")
    helpful_sections: List[str] = Field(..., description="Sections that were helpful")
    problematic_sections: List[str] = Field(..., description="Sections that had issues")
    general_comments: str = Field(..., description="General feedback comments")
    suggestions: str = Field(..., description="Suggestions for improvement")
    created_at: datetime = Field(..., description="When the feedback was created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "64f8b2a1c9e1234567890def",
                "username": "john_doe",
                "readme_history_id": "64f8b2a1c9e1234567890abc",
                "repository_name": "awesome-project",
                "rating": "good",
                "helpful_sections": ["Introduction", "Installation"],
                "problematic_sections": ["Usage"],
                "general_comments": "Overall good README but usage examples could be clearer",
                "suggestions": "Add more code examples in the Usage section",
                "created_at": "2024-01-15T10:35:00Z"
            }
        }


class FeedbackListResponse(BaseModel):
    """Model for feedback list response."""
    
    feedback: List[FeedbackResponse] = Field(..., description="List of feedback entries")
    total_count: int = Field(..., description="Total number of feedback entries")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of entries per page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback": [
                    {
                        "id": "64f8b2a1c9e1234567890def",
                        "username": "john_doe",
                        "readme_history_id": "64f8b2a1c9e1234567890abc",
                        "repository_name": "awesome-project",
                        "rating": "good",
                        "helpful_sections": ["Introduction"],
                        "problematic_sections": ["Usage"],
                        "general_comments": "Good overall",
                        "suggestions": "More examples needed",
                        "created_at": "2024-01-15T10:35:00Z"
                    }
                ],
                "total_count": 5,
                "page": 1,
                "page_size": 10
            }
        }


class FeedbackStats(BaseModel):
    """Model for feedback statistics."""
    
    total_feedback: int = Field(..., description="Total number of feedback entries")
    average_rating: float = Field(..., description="Average rating across all feedback")
    rating_distribution: dict = Field(..., description="Distribution of ratings")
    most_helpful_sections: List[dict] = Field(..., description="Most frequently helpful sections")
    most_problematic_sections: List[dict] = Field(..., description="Most frequently problematic sections")
    recent_feedback_count: int = Field(..., description="Feedback count in last 30 days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_feedback": 42,
                "average_rating": 4.2,
                "rating_distribution": {
                    "excellent": 10,
                    "good": 20,
                    "average": 8,
                    "poor": 3,
                    "terrible": 1
                },
                "most_helpful_sections": [
                    {"section": "Introduction", "count": 35},
                    {"section": "Installation", "count": 30}
                ],
                "most_problematic_sections": [
                    {"section": "Usage", "count": 15},
                    {"section": "API Reference", "count": 8}
                ],
                "recent_feedback_count": 12
            }
        }
