from typing import List, Optional
from pydantic import BaseModel, Field


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
    sections_included: List[str] = Field(
        ..., description="List of sections included in the README"
    )

    class Config:
        json_json_schema_extra = {
            "example": {
                "content": "# Project Name\n\n## Introduction\n\nThis is a brief introduction...",
                "sections_included": ["Introduction", "Installation"],
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
        default="Update README.md", description="Commit message"
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
