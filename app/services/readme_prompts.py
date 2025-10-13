from typing import Dict, Any
from app.schemas.readme import ReadmeSection


class ReadmePrompts:
    """Class containing all README generation prompt templates."""

    @staticmethod
    def get_common_guidelines() -> str:
        """Get common writing guidelines for all sections."""
        return """
        CRITICAL WRITING GUIDELINES - Write as a Senior Technical Writer:

        TONE & VOICE:
        - Write with authority and professionalism
        - Use active voice and imperative mood for instructions
        - Be direct and concise - every word must add value
        - Assume readers have basic technical knowledge
        - NEVER use first person (We/I/Our) - use second person (You) or third person (The project/This library)

        CONTENT QUALITY:
        - Be specific - provide exact versions, commands, and values
        - Avoid filler words and unnecessary explanations
        - Don't state the obvious (e.g., "You should clone using the URL below")
        - Use precise technical terminology
        - Focus on what users need to know, not what you want to say

        STRUCTURE:
        - Start with the most important information
        - Use clear headings and logical flow
        - Keep paragraphs short (2-4 sentences max)
        - Use lists for steps or multiple items
        - Use code blocks for all commands, code, and configuration

        WHAT TO AVOID:
        - Vague statements like "recent version", "as needed", "if applicable"
        - Redundant instructions or explanations
        - Flowery language or marketing speak
        - Overly casual phrases like "getting bogged down", "just run"
        - Apologetic or uncertain language
        """

    @staticmethod
    def get_base_repo_info(repo_info: Dict[str, Any]) -> str:
        """Get formatted repository information for prompts."""
        return f"""
        Repository Information:
        - Name: {repo_info.get('name', 'Unknown')}
        - Description: {repo_info.get('description', 'No description provided')}
        - Primary Language: {repo_info.get('language', 'Not specified')}
        - Clone URL: {repo_info.get('clone_url', 'https://github.com/username/repository.git')}
        - Topics/Tags: {', '.join(repo_info.get('topics', ['None']))}
        """

    @staticmethod
    def get_section_specific_prompt(
        section: ReadmeSection, repo_info: Dict[str, Any], all_sections: list = None
    ) -> str:
        """Get a section-specific prompt based on the section type."""
        base_info = ReadmePrompts.get_base_repo_info(repo_info)
        common_guidelines = ReadmePrompts.get_common_guidelines()
        section_name_lower = section.name.lower()

        # Map section names to their prompts
        section_prompts = {
            "introduction": {
                "instructions": """
            - Open with a single, clear sentence stating what the project does
            - State the specific problem or use case it addresses
            - Highlight 2-3 key benefits or value propositions
            - Maximum 2-3 short paragraphs
            - Avoid marketing language, flowery introductions, or background stories"""
            },
            "table of contents": {
                "instructions": """
            - Create markdown links to ALL sections that will appear in the README
            - Use a bulleted list format with proper anchor links
            - Link format: [Section Name](#section-name) where section-name is lowercase with hyphens and spaces replaced
            - Include all H2 (##) sections that come AFTER this Table of Contents
            - Do NOT include the Table of Contents itself in the links
            - Order links to match the actual section order in the document
            - Example format:
              - [Introduction](#introduction)
              - [Features](#features)
              - [Installation](#installation)
            - Keep it clean and simple - no decorations or emojis"""
            },
            "features": {
                "instructions": """
            - Use concise bullet points (one line per feature)
            - State user-facing capabilities, not implementation details
            - Be specific - avoid vague terms like "powerful" or "flexible"
            - Focus on what users can accomplish
            - Group related features with sub-bullets if needed"""
            },
            "tech stack": {
                "instructions": """
            - Identify and list primary technologies from repository files (package.json, requirements.txt, go.mod, Cargo.toml, etc.)
            - Include version numbers if clearly specified in dependency files
            - Organize by category (Backend, Frontend, Database, DevOps, Testing, etc.)
            - Use bullet points with framework/library names
            - Focus on major dependencies only (5-10 key technologies)
            - Do NOT leave this section empty - analyze the repository to find technologies
            - If using badges, include them for major frameworks/languages"""
            },
            "prerequisites": {
                "instructions": """
            - List required software with minimum version numbers
            - Include system requirements if relevant
            - Mention accounts or API keys needed
            - Use bullet points for clarity
            - Separate required vs optional prerequisites"""
            },
            "installation": {
                "instructions": """
            - Provide numbered steps in logical order
            - Include git clone command with the repository URL
            - Show package installation commands (npm install, pip install -r requirements.txt, etc.)
            - Include database setup/migrations if applicable
            - Include environment variable setup if needed
            - One code block per distinct step
            - STOP after installation is complete - do NOT include running the application
            - Do NOT repeat steps that belong in Usage section (like running servers or creating users)"""
            },
            "configuration": {
                "instructions": """
            - List configuration options in a table format
            - Include: option name, type, default value, description
            - Show example configuration files
            - Document environment variables with examples
            - Explicitly mark required vs optional settings"""
            },
            "usage": {
                "instructions": """
            - START with how to run the application (e.g., npm start, python manage.py runserver)
            - Show the simplest working example of using the project
            - Provide actual, runnable code samples (not pseudocode)
            - Include necessary imports or setup for code examples
            - Demonstrate 2-3 common use cases with code
            - Use appropriate language syntax highlighting
            - Show expected output only if it adds value
            - Do NOT repeat installation steps - assume installation is already complete
            - Focus on "how to use" not "how to install"""
            },
            "api reference": {
                "instructions": """
            - Document key endpoints, functions, or classes
            - Use consistent format: signature, parameters, return value, example
            - Include HTTP methods and routes for REST APIs
            - Show request/response examples
            - Provide type information where applicable
            - Keep descriptions technical and precise"""
            },
            "project structure": {
                "instructions": """
            - Display directory tree of key folders and files
            - Use code block with tree-like formatting
            - Add brief descriptions for important directories
            - Focus on what developers need to know
            - Explain purpose of main configuration files"""
            },
            "testing": {
                "instructions": """
            - Provide commands to run tests
            - List test frameworks/runners used
            - Explain different test types if applicable (unit, integration, e2e)
            - Show how to run specific test suites
            - Include coverage commands if available"""
            },
            "deployment": {
                "instructions": """
            - Provide deployment steps in sequential order
            - Specify target platforms (Vercel, Heroku, AWS, Docker, etc.)
            - Include build/compilation commands
            - Show environment variable configuration
            - Link to platform-specific documentation if needed"""
            },
            "contributing": {
                "instructions": """
            - State how to report issues and submit PRs
            - Provide development setup steps
            - Describe coding standards or style guide
            - Explain branch naming and commit conventions
            - Be welcoming but professional"""
            },
            "license": {
                "instructions": """
            - State license type prominently at the top
            - Link to LICENSE file ONLY if it exists (check license_file field)
            - Briefly explain key permissions and restrictions
            - No placeholder links to non-existent files
            - Keep it factual - no legal interpretation""",
                "context": ReadmePrompts._get_license_context(repo_info),
            },
        }

        # Get the prompt configuration for this section
        prompt_config = section_prompts.get(section_name_lower)

        if prompt_config:
            context = prompt_config.get("context", "")
            instructions = prompt_config.get("instructions", "")

            if section_name_lower == "table of contents" and all_sections:
                sections_list = "\n\nSections to include in Table of Contents:\n"
                for s in all_sections:
                    if s.name.lower() != "table of contents":
                        sections_list += f"- {s.name}\n"
                context += sections_list

            return f"""
            Create ONLY the "{section.name}" section for this README.

            {base_info}
            {context}
            This section should:{instructions}

            {common_guidelines}

            Format as: ## {section.name}
            """
        else:
            # Generic fallback for custom or unrecognized sections
            return f"""
            Create ONLY the "{section.name}" section for this README.

            {base_info}

            Section Description: {section.description}

            This section should address the described purpose while being:
            - Clear and actionable
            - Relevant to the project
            - Well-formatted in Markdown

            {common_guidelines}

            Format as: ## {section.name}
            """

    @staticmethod
    def _get_license_context(repo_info: Dict[str, Any]) -> str:
        """Get license context for the license section."""
        license_info = "\nAdditional License Information:\n"
        if repo_info.get("license"):
            license_info += f"- License Type: {repo_info.get('license')}\n            "
        if repo_info.get("license_file"):
            license_info += f"- License File: {repo_info.get('license_file')} (exists in repository)\n            "
        else:
            license_info += "- No license file found in repository root\n            "
        return license_info

    @staticmethod
    def get_header_prompt(repo_info: Dict[str, Any]) -> str:
        """Get the prompt for generating README header section."""
        base_info = ReadmePrompts.get_base_repo_info(repo_info)
        common_guidelines = ReadmePrompts.get_common_guidelines()

        return f"""
        Create only the header section of a README.md for the GitHub repository: {repo_info.get('name')}

        {base_info}

        REQUIREMENTS:
        1. Start with H1 title: # {repo_info.get('name', 'Project Name')}
        2. Add a brief one-sentence description of what the project does (plain text, not a heading)
        3. Include relevant badges if appropriate (build status, version, license, language, etc.)

        FORMAT:
        # Project Name
        Brief one-line description here.

        [Badges here if applicable]

        {common_guidelines}

        IMPORTANT:
        - The H1 title MUST be the first line
        - ONLY include the header section, no other sections like Introduction or Table of Contents
        - Do NOT add any ## headings in this section
        """
