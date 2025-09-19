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

        # Section-specific prompts
        if section_name_lower in ["introduction", "overview"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Start with a compelling one-sentence description of what this project does
            - Explain the main problem it solves or need it addresses
            - Highlight 2-3 key benefits or features
            - Keep it concise (2-3 paragraphs maximum)
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower == "installation":
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should provide clear, step-by-step installation instructions:
            - Start with cloning the repository using the actual clone URL provided above
            - List any prerequisites (Node.js version, Python version, etc.)
            - Provide specific commands for the detected language/framework
            - Include package manager commands (npm, pip, etc.)
            - Add environment setup if needed
            - Use code blocks for all commands
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["usage", "getting started"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Provide a quick start example
            - Show the most common use case with working code
            - Include import/require statements
            - Show expected output where relevant
            - Use proper code formatting with language tags
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["features", "capabilities"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - List key features in bullet points or numbered list
            - Focus on user benefits, not technical implementation details
            - Use action-oriented language
            - Keep each feature description to 1-2 lines
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["api reference", "api", "api documentation"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Document main classes, functions, or endpoints
            - Include parameter descriptions and return values
            - Provide code examples for each API element
            - Use proper code formatting
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["configuration", "config", "setup"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Explain available configuration options
            - Show configuration file examples
            - Explain environment variables if applicable
            - Provide default values where relevant
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["contributing", "contribution"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Explain how others can contribute
            - List steps for setting up development environment
            - Mention coding standards or guidelines
            - Explain pull request process
            - Be welcoming and encouraging
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["testing", "tests"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Explain how to run the test suite
            - Provide specific test commands
            - Mention test frameworks used
            - Explain how to run different types of tests (unit, integration, etc.)
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["deployment", "deploy"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Explain deployment process step by step
            - Mention deployment platforms or requirements
            - Include build commands if needed
            - Provide environment-specific instructions
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in [
            "project structure",
            "file structure",
            "organization",
        ]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            Additional Context:
            {repo_info.get('file_structure', 'File structure not available')}
            
            This section should:
            - Explain the purpose of main directories and files
            - Use a tree structure or organized list
            - Focus on files/folders users need to know about
            - Keep explanations brief and clear
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["examples", "more examples"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - Provide multiple practical examples
            - Show different use cases or scenarios
            - Include complete, working code samples
            - Explain what each example demonstrates
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        elif section_name_lower in ["license", "licensing"]:
            return f"""
            Create ONLY the "{section.name}" section for this README.
            
            {base_info}
            
            This section should:
            - State the license type clearly
            - Include standard license badge if appropriate
            - Mention any licensing restrictions or permissions
            - Keep it brief and factual
            
            {common_guidelines}
            
            Format as: ## {section.name}
            """

        else:
            # Generic fallback for custom sections
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
    def get_full_readme_prompt(
        repo_info: Dict[str, Any],
        sections,
        file_structure: str = "",
        code_samples: str = "",
    ) -> str:
        """Get the prompt for generating a complete README in one call."""
        # Format sections for the prompt
        section_descriptions = "\n".join(
            [f"- {section.name}: {section.description}" for section in sections]
        )

        return f"""
        # TASK
        You are an expert technical writer specializing in creating clear, professional, and comprehensive README documentation for software projects.

        Create a README.md for a GitHub repository with the following information:

        # REPOSITORY INFORMATION
        - Name: {repo_info.get('name', 'Unknown')}
        - Description: {repo_info.get('description', 'No description provided')}
        - Primary Language: {repo_info.get('language', 'Not specified')}
        - Clone URL: {repo_info.get('clone_url', 'https://github.com/username/repository.git')}
        - Topics/Tags: {', '.join(repo_info.get('topics', ['None']))}

        # FILE STRUCTURE
        {file_structure}

        {code_samples}

        # REQUIRED SECTIONS
        The README should contain the following sections:
        {section_descriptions}

        # CRITICAL WRITING GUIDELINES
        1. Use second person for instructions (You can/should) and neutral imperative commands (Install the package, Run the tests)
        2. Use third person where appropriate (This project provides, The application supports)
        3. NEVER use first person (We/I/Our)
        4. Write directly to users with clear, actionable instructions
        5. Use active voice and direct commands (e.g., "Install the package" not "The package can be installed")
        6. Be specific and actionable - avoid vague statements
        7. Use professional, clear, and concise language
        8. Follow Markdown best practices with proper headings, lists, code blocks, etc.
        9. For installation and usage sections, use real commands based on the repo's language/framework
        10. Provide concrete examples where possible
        11. Format the output as a valid Markdown document
        12. Do not include sections that are not requested

        # OUTPUT FORMAT
        Respond with ONLY the README.md content in Markdown format, without any additional explanation or conversation.
        """

    @staticmethod
    def get_header_prompt(repo_info: Dict[str, Any]) -> str:
        """Get the prompt for generating README header section."""
        return f"""
        Create only the header section of a README.md for the GitHub repository: {repo_info.get('name')}

        Repository Information:
        - Name: {repo_info.get('name', 'Unknown')}
        - Description: {repo_info.get('description', 'No description provided')}
        - Primary Language: {repo_info.get('language', 'Not specified')}
        - Clone URL: {repo_info.get('clone_url', 'https://github.com/username/repository.git')}

        Include:
        1. A title (H1 heading with the repository name)
        2. A brief one-paragraph description of what the project does
        3. Appropriate badges if needed (build status, version, license, etc.)

        CRITICAL WRITING GUIDELINES:
        - Use second person for instructions (You can/should) and neutral imperative commands (Install the package, Run the tests)
        - Use third person where appropriate (This project provides, The application supports)
        - NEVER use first person (We/I/Our)
        - Write directly to users with clear, actionable instructions
        - Use active voice and direct commands
        - Be specific and actionable
        - Avoid vague statements like "We don't know" or "From what I can see"

        Format the output as Markdown. ONLY include the header section, no other sections.
        """
