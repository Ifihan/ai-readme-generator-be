from typing import Dict, Any
from app.schemas.readme import ReadmeSection


class ReadmePrompts:
    """Class containing all README generation prompt templates."""

    @staticmethod
    def get_common_guidelines() -> str:
        """Get common writing guidelines for all sections."""
        return """
        CRITICAL WRITING GUIDELINES:
        - Use second person for instructions (You can/should) and neutral imperative commands (Install the package, Run the tests)
        - Use third person where appropriate (This project provides, The application supports)
        - NEVER use first person (We/I/Our)
        - Write directly to users with clear, actionable instructions
        - Use active voice and direct commands
        - Be specific and actionable
        - Avoid vague statements like "We don't know" or "From what I can see"
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
        section: ReadmeSection, repo_info: Dict[str, Any]
    ) -> str:
        """Get a section-specific prompt based on the section type."""
        base_info = ReadmePrompts.get_base_repo_info(repo_info)
        common_guidelines = ReadmePrompts.get_common_guidelines()
        section_name_lower = section.name.lower()

        # Map section names to their prompts
        section_prompts = {
            "introduction": {
                "instructions": """
            - Start with a compelling one-sentence description of what this project does
            - Explain the main problem it solves or need it addresses
            - Highlight 2-3 key benefits or features
            - Keep it concise (2-3 paragraphs maximum)"""
            },
            "installation": {
                "instructions": """
            - Start with cloning the repository using the actual clone URL provided above
            - List any prerequisites (Node.js version, Python version, etc.)
            - Provide specific commands for the detected language/framework
            - Include package manager commands (npm, pip, etc.)
            - Add environment setup if needed
            - Use code blocks for all commands"""
            },
            "usage": {
                "instructions": """
            - Provide a quick start example
            - Show the most common use case with working code
            - Include import/require statements
            - Show expected output where relevant
            - Use proper code formatting with language tags"""
            },
            "features": {
                "instructions": """
            - List key features in bullet points or numbered list
            - Focus on user benefits, not technical implementation details
            - Use action-oriented language
            - Keep each feature description to 1-2 lines"""
            },
            "api reference": {
                "instructions": """
            - Document main classes, functions, or endpoints
            - Include parameter descriptions and return values
            - Provide code examples for each API element
            - Use proper code formatting"""
            },
            "configuration": {
                "instructions": """
            - Explain available configuration options
            - Show configuration file examples
            - Explain environment variables if applicable
            - Provide default values where relevant"""
            },
            "contributing": {
                "instructions": """
            - Explain how others can contribute
            - List steps for setting up development environment
            - Mention coding standards or guidelines
            - Explain pull request process
            - Be welcoming and encouraging"""
            },
            "testing": {
                "instructions": """
            - Explain how to run the test suite
            - Provide specific test commands
            - Mention test frameworks used
            - Explain how to run different types of tests (unit, integration, etc.)"""
            },
            "deployment": {
                "instructions": """
            - Explain deployment process step by step
            - Mention deployment platforms or requirements
            - Include build commands if needed
            - Provide environment-specific instructions"""
            },
            "examples": {
                "instructions": """
            - Provide multiple practical examples
            - Show different use cases or scenarios
            - Include complete, working code samples
            - Explain what each example demonstrates"""
            },
            "license": {
                "instructions": """
            - State the license type clearly (use the license type from repository information if available)
            - ONLY link to license file if one actually exists in the repository (license_file field above)
            - If no license file exists, do NOT create a link to LICENSE.md or similar
            - Include standard license badge if appropriate
            - Mention any licensing restrictions or permissions
            - Keep it brief and factual""",
                "context": ReadmePrompts._get_license_context(repo_info)
            },
            "roadmap": {
                "instructions": """
            - Outline planned features and improvements
            - Organize by timeline or priority
            - Be realistic about deliverables
            - Include links to relevant issues or discussions if available"""
            },
            "acknowledgements": {
                "instructions": """
            - Credit libraries, tools, and frameworks used
            - Acknowledge contributors and supporters
            - Include links where appropriate
            - Be genuine and specific"""
            },
            "faq": {
                "instructions": """
            - Answer common questions users might have
            - Use clear Q&A format
            - Address installation, usage, and troubleshooting topics
            - Keep answers concise but complete"""
            }
        }

        # Get the prompt configuration for this section
        prompt_config = section_prompts.get(section_name_lower)

        if prompt_config:
            context = prompt_config.get("context", "")
            instructions = prompt_config.get("instructions", "")

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
        if repo_info.get('license'):
            license_info += f"- License Type: {repo_info.get('license')}\n            "
        if repo_info.get('license_file'):
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

        Include:
        1. A title (H1 heading with the repository name)
        2. A brief one-paragraph description of what the project does
        3. Appropriate badges if needed (build status, version, license, etc.)

        {common_guidelines}

        Format the output as Markdown. ONLY include the header section, no other sections.
        """
