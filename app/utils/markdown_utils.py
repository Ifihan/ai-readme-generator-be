import re
from typing import List, Dict, Any, Tuple, Optional


def extract_sections_from_markdown(markdown_text: str) -> Dict[str, str]:
    """
    Extract sections from a markdown document based on headings.
    """
    if not markdown_text:
        return {}

    # Split the text by headings (# Heading)
    pattern = r"^(#{1,3})\s+(.+?)$"

    lines = markdown_text.split("\n")
    sections = {}
    current_section = None
    current_content = []

    for line in lines:
        heading_match = re.match(pattern, line, re.MULTILINE)

        if heading_match:
            # If we were processing a section before, save it
            if current_section is not None:
                sections[current_section] = "\n".join(current_content).strip()

            # Start a new section
            current_section = heading_match.group(2).strip()
            current_content = []
        else:
            if current_section is not None:
                current_content.append(line)
            else:
                # Content before any heading goes into the "Intro" section
                if not current_content:
                    current_section = "Intro"
                current_content.append(line)

    # Save the last section
    if current_section is not None:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def merge_markdown_sections(sections: Dict[str, str]) -> str:
    """
    Merge markdown sections into a single document.
    """
    result = []

    # Handle intro section (no heading)
    if "Intro" in sections:
        result.append(sections["Intro"])

    # Add all other sections with headings
    for section, content in sections.items():
        if section != "Intro":
            result.append(f"## {section}\n\n{content}")

    return "\n\n".join(result)


def format_readme_metadata(repo_info: Dict[str, Any]) -> str:
    """
    Format repository metadata for the README.
    """
    metadata = []

    # Title
    name = repo_info.get("name", "")
    metadata.append(f"# {name}")

    # Description
    description = repo_info.get("description")
    if description:
        metadata.append(description)

    # Generate badges
    badges = []
    language = repo_info.get("language")
    if language:
        badges.append(
            f"![Language](https://img.shields.io/badge/Language-{language}-blue)"
        )

    license_info = repo_info.get("license", {})
    if license_info and license_info.get("name"):
        license_name = license_info["name"]
        badges.append(
            f"![License](https://img.shields.io/badge/License-{license_name.replace(' ', '%20')}-green)"
        )

    if badges:
        metadata.append(" ".join(badges))

    return "\n\n".join(metadata)


def identify_readme_sections(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Identify standard README sections from markdown.
    """
    sections = extract_sections_from_markdown(markdown_text)

    # Map of section titles to standardized keys
    section_mapping = {
        # Title variations
        "title": ["title", "project name", "project title"],
        # Description variations
        "description": ["description", "about", "overview", "introduction", "summary"],
        # Installation variations
        "installation": [
            "installation",
            "getting started",
            "setup",
            "install",
            "quick start",
        ],
        # Usage variations
        "usage": ["usage", "using", "how to use", "examples", "example usage"],
        # Features variations
        "features": ["features", "key features", "functionality", "capabilities"],
        # API variations
        "api": ["api", "api documentation", "endpoints", "api reference"],
        # Configuration variations
        "configuration": [
            "configuration",
            "config",
            "settings",
            "environment variables",
            "env vars",
        ],
        # Contributing variations
        "contributing": [
            "contributing",
            "contribution guidelines",
            "how to contribute",
        ],
        # Testing variations
        "testing": ["testing", "tests", "how to test", "test"],
        # Deployment variations
        "deployment": ["deployment", "deploy", "publishing", "release"],
        # License variations
        "license": ["license", "licensing", "copyright"],
        # Acknowledgements variations
        "acknowledgements": [
            "acknowledgements",
            "credits",
            "thanks",
            "acknowledgments",
        ],
    }

    standardized_sections = []

    # Normalize section titles and add them to the result
    for section_title, content in sections.items():
        title_lower = section_title.lower()

        matched = False
        for std_key, variations in section_mapping.items():
            if any(variation in title_lower for variation in variations):
                standardized_sections.append(
                    {
                        "id": std_key,
                        "title": section_title,
                        "content": content,
                        "length": len(content),
                    }
                )
                matched = True
                break

        if not matched and title_lower != "intro":
            # Add as custom section
            standardized_sections.append(
                {
                    "id": f"custom_{len(standardized_sections)}",
                    "title": section_title,
                    "content": content,
                    "length": len(content),
                    "custom": True,
                }
            )

    return standardized_sections


def generate_toc(sections: List[Dict[str, Any]]) -> str:
    """
    Generate a table of contents from sections.
    """
    if not sections:
        return ""

    toc = ["## Table of Contents\n"]

    for i, section in enumerate(sections):
        # Create a link-friendly version of the title
        link = section["title"].lower().replace(" ", "-").replace(".", "")
        toc.append(f"{i+1}. [{section['title']}](#{link})")

    return "\n".join(toc)


def get_recommended_sections(repo_info: Dict[str, Any]) -> List[str]:
    """
    Get recommended README sections based on repository information.
    """
    sections = ["title", "description", "installation", "usage", "license"]

    # Add language-specific sections
    language = repo_info.get("language", "").lower()

    if language in ["python", "javascript", "typescript", "ruby", "php"]:
        sections.append("testing")

    if language in ["javascript", "typescript", "python", "ruby", "go"]:
        sections.append("contributing")

    # API documentation for web languages
    if language in ["javascript", "typescript", "python", "ruby", "php", "go", "java"]:
        has_web_frameworks = False

        files = repo_info.get("files", [])
        file_paths = [f.get("path", "").lower() for f in files]

        # Check for web framework files
        web_frameworks = [
            # Python
            "django",
            "flask",
            "fastapi",
            "tornado",
            "bottle",
            "pyramid",
            # JavaScript/TypeScript
            "express",
            "koa",
            "hapi",
            "fastify",
            "next",
            "nuxt",
            "nest",
            # Ruby
            "rails",
            "sinatra",
            "hanami",
            # PHP
            "laravel",
            "symfony",
            "slim",
            "lumen",
            # Go
            "gin",
            "echo",
            "fiber",
            "gorilla",
            # Java
            "spring",
            "quarkus",
            "micronaut",
            "jersey",
        ]

        if any(framework in " ".join(file_paths) for framework in web_frameworks):
            has_web_frameworks = True

        if has_web_frameworks:
            sections.append("api_documentation")

    return sections
