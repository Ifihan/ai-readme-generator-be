from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


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
        description="Brief overview of what the project does and its key features",
        is_default=True,
        order=1,
    ),
    SectionTemplate(
        id="installation",
        name="Installation",
        description="Step-by-step instructions for installing the project",
        is_default=True,
        order=2,
    ),
    SectionTemplate(
        id="usage",
        name="Usage",
        description="Examples of how to use the project with code samples",
        is_default=True,
        order=3,
    ),
    SectionTemplate(
        id="api_reference",
        name="API Reference",
        description="Documentation of the project's API (if applicable)",
        is_default=False,
        order=4,
    ),
    SectionTemplate(
        id="features",
        name="Features",
        description="Detailed list of features and capabilities",
        is_default=True,
        order=5,
    ),
    SectionTemplate(
        id="configuration",
        name="Configuration",
        description="Information about how to configure the project",
        is_default=False,
        order=6,
    ),
    SectionTemplate(
        id="roadmap",
        name="Roadmap",
        description="Future plans and upcoming features",
        is_default=False,
        order=7,
    ),
    SectionTemplate(
        id="contributing",
        name="Contributing",
        description="Guidelines for contributing to the project",
        is_default=True,
        order=8,
    ),
    SectionTemplate(
        id="license",
        name="License",
        description="Licensing information for the project",
        is_default=False,
        order=9,
    ),
    SectionTemplate(
        id="acknowledgements",
        name="Acknowledgements",
        description="Credits and acknowledgements for libraries, tools, or contributors",
        is_default=False,
        order=10,
    ),
    SectionTemplate(
        id="project_structure",
        name="Project Structure",
        description="Overview of the project's file and directory structure",
        is_default=False,
        order=11,
    ),
    SectionTemplate(
        id="faq",
        name="FAQ",
        description="Frequently asked questions about the project",
        is_default=False,
        order=12,
    ),
    SectionTemplate(
        id="testing",
        name="Testing",
        description="Information about how to run tests",
        is_default=False,
        order=13,
    ),
    SectionTemplate(
        id="deployment",
        name="Deployment",
        description="Instructions for deploying the project to production",
        is_default=False,
        order=14,
    ),
    SectionTemplate(
        id="examples",
        name="Examples",
        description="More detailed examples of how to use the project",
        is_default=False,
        order=15,
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
