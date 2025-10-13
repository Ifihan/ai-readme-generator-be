from typing import List, Dict, Any
import logging
import os
import re
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from app.schemas.readme import ReadmeSection, ReadmeGenerationRequest
from app.services.github_service import GitHubService
from app.services.readme_prompts import ReadmePrompts
from app.utils.markdown_utils import (
    extract_sections_from_markdown,
    merge_markdown_sections,
)
from app.exceptions import GeminiApiException
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google's Gemini API through LangChain."""

    def __init__(self, api_key: str = None):
        """Initialize the Gemini service with API key."""
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Google API Key is required for Gemini Service")

        # Initialize with default settings
        self.default_max_tokens = 4096
        self.max_fallback_tokens = 8192
        self.temperature = 0.2

        # Initialize the Gemini model with LangChain wrapper
        self.llm = self._create_llm(self.default_max_tokens)

        # Create conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

    def _create_llm(self, max_tokens: int) -> ChatGoogleGenerativeAI:
        """Create a Gemini LLM instance with specified token limit."""
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=self.api_key,
            temperature=self.temperature,
            max_output_tokens=max_tokens,
        )

    async def generate_readme(
        self, request: ReadmeGenerationRequest, github_service: GitHubService
    ) -> str:
        """Generate a README for a GitHub repository with automatic fallback handling."""
        # Get repository information
        repo_info = await github_service.get_repository_details(request.repository_url)

        # Check for existing README first
        owner, repo = github_service._parse_repo_url(request.repository_url)
        existing_readme = await github_service.get_existing_readme(owner, repo)

        # If existing README found, improve it instead of creating from scratch
        if existing_readme["exists"] and existing_readme["content"]:
            logger.info(
                f"Found existing README ({existing_readme['filename']}) - will improve it"
            )

            # Create improvement instructions based on requested sections
            section_names = [section.name for section in request.sections]
            improvement_feedback = f"""
            Please improve this existing README by enhancing or adding the following sections: {', '.join(section_names)}.
            
            Repository Information:
            - Name: {repo_info.get('name', 'Unknown')}
            - Description: {repo_info.get('description', 'No description provided')}
            - Primary Language: {repo_info.get('language', 'Not specified')}
            - Clone URL: {repo_info.get('clone_url', 'https://github.com/username/repository.git')}
            - License: {repo_info.get('license', 'Not specified')}
            - License File: {repo_info.get('license_file', 'None found')}
            
            Guidelines:
            - Keep good existing content but enhance it
            - Add missing sections from the requested list
            - Improve existing sections to be more comprehensive and professional
            - Use the repository information above for accuracy
            - Only link to license files that actually exist
            - Follow modern README best practices
            """

            return await self.refine_readme(
                existing_readme["content"], improvement_feedback
            )

        # Get file structure if needed
        if any(
            section.name.lower() == "project structure" for section in request.sections
        ):
            file_structure = await github_service.get_repository_file_structure(
                request.repository_url
            )
            repo_info["file_structure"] = file_structure

        # Get code samples if needed for examples sections
        if any(
            section.name.lower() in ["usage", "examples", "getting started"]
            for section in request.sections
        ):
            code_samples = await github_service.get_code_samples(request.repository_url)
            repo_info["code_samples"] = code_samples

        # Generate README section-by-section
        return await self._generate_readme_by_section(repo_info, request.sections)

    def _filter_to_requested_sections(
        self, content: str, sections: List[ReadmeSection]
    ) -> str:
        """Filter README content to only include requested sections."""
        requested_section_names = {section.name.lower() for section in sections}

        # Split content into lines for processing
        lines = content.split("\n")
        filtered_lines = []
        current_section = None
        include_current_section = True

        for line in lines:
            # Check if this line is a heading
            if line.strip().startswith("#"):
                # Extract section name from heading
                heading_text = line.strip().lstrip("#").strip()
                current_section = heading_text.lower()

                # Check if this section was requested
                include_current_section = any(
                    req_section in current_section or current_section in req_section
                    for req_section in requested_section_names
                )

                if include_current_section:
                    filtered_lines.append(line)
            else:
                # Include content only if we're in a requested section
                if include_current_section:
                    filtered_lines.append(line)

        # If no sections were found or content is too short, return original
        if len(filtered_lines) < 5:
            logger.warning(
                "Section filtering resulted in very short content, returning original"
            )
            return content

        return "\n".join(filtered_lines)

    async def _generate_readme_by_section(
        self, repo_info: Dict[str, Any], sections: List[ReadmeSection]
    ) -> str:
        """Generate README content section by section."""
        # Start with the header section (title, badges, short description)
        header_prompt = ReadmePrompts.get_header_prompt(repo_info)
        header_prompt_template = ChatPromptTemplate.from_template(header_prompt)
        header_chain = header_prompt_template | self.llm | StrOutputParser()
        header_content = await header_chain.ainvoke({})

        # Generate each section separately using section-specific prompts
        sections_content = []
        for section in sorted(sections, key=lambda x: x.order):
            # Handle project structure section without AI - just use the tree directly
            if section.name.lower() == "project structure":
                file_structure = repo_info.get("file_structure", "")
                if file_structure:
                    section_content = f"## {section.name}\n\n```\n{file_structure}\n```"
                    sections_content.append(section_content)
                else:
                    sections_content.append(
                        f"\n## {section.name}\n\n*File structure not available.*\n"
                    )
                continue

            # Get section-specific prompt for AI-generated sections
            section_prompt = ReadmePrompts.get_section_specific_prompt(
                section, repo_info, sections
            )

            # Add code samples context if relevant for the section
            if section.name.lower() in ["usage", "examples", "getting started"]:
                sample_files = repo_info.get("code_samples", {})
                if sample_files:
                    code_context = "\n\nCode Samples for Reference:\n"
                    for file_path, content in sample_files.items():
                        # Escape curly braces in code content by doubling them
                        escaped_content = (
                            content[:500].replace("{", "{{").replace("}", "}}")
                        )
                        code_context += (
                            f"\nFile: {file_path}\n```\n{escaped_content}...\n```\n"
                        )
                    section_prompt += code_context

            section_prompt_template = ChatPromptTemplate.from_template(section_prompt)
            section_chain = section_prompt_template | self.llm | StrOutputParser()

            try:
                section_content = await section_chain.ainvoke({})
                sections_content.append(section_content)
            except Exception as e:
                logger.error(f"Error generating section {section.name}: {str(e)}")
                # Add a placeholder for failed sections
                sections_content.append(
                    f"\n## {section.name}\n\n*Content generation failed for this section.*\n"
                )

        # Combine all sections
        full_content = header_content + "\n\n" + "\n\n".join(sections_content)

        # Apply filtering to ensure only requested sections are included
        filtered_content = self._filter_to_requested_sections(full_content, sections)

        return filtered_content

    async def refine_readme(self, readme_content: str, feedback: str) -> str:
        """Refine a generated README based on user feedback with fallback mechanism."""
        # First attempt with default token limit
        try:
            return await self._refine_readme_standard(readme_content, feedback)
        except Exception as e:
            logger.warning(
                f"Initial README refinement failed: {str(e)}. Trying with increased token limit..."
            )

            # Second attempt with increased token limit
            try:
                # Create a higher-capacity model
                original_llm = self.llm
                self.llm = self._create_llm(self.max_fallback_tokens)

                result = await self._refine_readme_standard(readme_content, feedback)

                # Restore original model
                self.llm = original_llm
                return result
            except Exception as e2:
                logger.warning(
                    f"Increased token limit refinement failed: {str(e2)}. Attempting targeted refinement..."
                )

                # Third attempt: Targeted refinement
                # Restore original model if needed
                self.llm = original_llm
                return await self._refine_readme_targeted(readme_content, feedback)

    async def _refine_readme_standard(self, readme_content: str, feedback: str) -> str:
        """Standard approach to refine the entire README at once."""
        # Escape any curly braces in the readme content that might cause f-string issues
        escaped_readme_content = readme_content.replace("{", "{{").replace("}", "}}")

        prompt = f"""
        You are an expert technical writer specializing in improving README documentation.

        Below is a README.md file that needs to be refined based on user feedback:

        ```markdown
        {escaped_readme_content}
        ```

        User feedback:
        {feedback}

        Please revise the README to address this feedback while maintaining professional quality, proper Markdown formatting, and comprehensive coverage of the project.

        Respond with ONLY the revised README.md content in Markdown format, without any additional explanation or conversation.
        """

        prompt_template = ChatPromptTemplate.from_template(prompt)
        chain = prompt_template | self.llm | StrOutputParser()

        refined_content = await chain.ainvoke({})

        # Check for truncation
        if refined_content.endswith("...") or refined_content.endswith("…"):
            raise ValueError("Refinement appears to be truncated")

        return refined_content

    async def _refine_readme_targeted(self, readme_content: str, feedback: str) -> str:
        """Targeted approach to refine specific sections of the README."""
        # Escape any curly braces in the readme content that might cause f-string issues
        escaped_readme_content = readme_content.replace("{", "{{").replace("}", "}}")

        # First, analyze the feedback to identify which sections need refinement
        analyze_prompt = f"""
        Analyze the following feedback for a README.md file and identify which specific sections need to be refined.

        README feedback:
        {feedback}

        Respond with ONLY a comma-separated list of section names that need to be refined.
        If the feedback is general or applies to the entire document, respond with "ALL".
        Do not include any other text in your response.
        """

        analyze_template = ChatPromptTemplate.from_template(analyze_prompt)
        analyze_chain = analyze_template | self.llm | StrOutputParser()

        try:
            sections_to_refine = await analyze_chain.ainvoke({}).strip()

            if sections_to_refine.upper() == "ALL":
                # If feedback applies to everything, try a different approach
                # Split the README into chunks and refine each chunk
                chunks = self._split_readme_into_chunks(readme_content)
                refined_chunks = []

                for chunk in chunks:
                    # Escape any curly braces in the chunk
                    escaped_chunk = chunk.replace("{", "{{").replace("}", "}}")
                    refine_chunk_prompt = f"""
                    Refine the following portion of a README.md file based on this feedback:

                    Feedback: {feedback}

                    README portion:
                    ```markdown
                    {escaped_chunk}
                    ```

                    Respond with ONLY the refined portion in Markdown format.
                    Maintain all section headings and structure exactly as they appear.
                    """

                    chunk_template = ChatPromptTemplate.from_template(
                        refine_chunk_prompt
                    )
                    chunk_chain = chunk_template | self.llm | StrOutputParser()

                    refined_chunk = await chunk_chain.ainvoke({})
                    refined_chunks.append(refined_chunk)

                return "\n\n".join(refined_chunks)
            else:
                # Extract the sections to refine
                section_names = [name.strip() for name in sections_to_refine.split(",")]

                # Extract sections from the README
                sections = extract_sections_from_markdown(readme_content)

                # Refine each identified section
                for section_name in section_names:
                    if section_name in sections:
                        section_content = sections[section_name]
                        # Escape any curly braces in the section content
                        escaped_section_content = section_content.replace(
                            "{", "{{"
                        ).replace("}", "}}")

                        refine_section_prompt = f"""
                        Refine the following section of a README.md file based on this feedback:

                        Feedback: {feedback}

                        Section: {section_name}
                        ```markdown
                        {escaped_section_content}
                        ```

                        Respond with ONLY the refined section in Markdown format.
                        Maintain the section heading exactly as it appears.
                        """

                        section_template = ChatPromptTemplate.from_template(
                            refine_section_prompt
                        )
                        section_chain = section_template | self.llm | StrOutputParser()

                        refined_section = await section_chain.ainvoke({})
                        sections[section_name] = refined_section

                # Reconstruct the README
                return merge_markdown_sections(sections)
        except Exception as e:
            logger.error(f"Error in targeted refinement: {str(e)}")
            # Fallback to minimal refinement
            return self._minimal_refinement(readme_content, feedback)

    def _split_readme_into_chunks(self, readme_content: str) -> List[str]:
        """Split README content into manageable chunks."""
        # Split by top-level headings (# Heading)
        heading_pattern = re.compile(r"^# ", re.MULTILINE)
        split_positions = [
            match.start() for match in heading_pattern.finditer(readme_content)
        ]

        if not split_positions:
            # If no top-level headings, return the whole README as a single chunk
            return [readme_content]

        # Add the start position
        if split_positions[0] > 0:
            split_positions.insert(0, 0)
        else:
            split_positions[0] = 0

        # Add the end position
        split_positions.append(len(readme_content))

        # Create chunks
        chunks = []
        for i in range(len(split_positions) - 1):
            start = split_positions[i]
            end = split_positions[i + 1]
            chunk = readme_content[start:end].strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    def _minimal_refinement(self, readme_content: str, feedback: str) -> str:
        """Perform minimal refinement as a final fallback."""
        # Add a note about the feedback at the top of the README
        note = f"""<!--
        Feedback received:
        {feedback}

        This README requires further refinement based on the feedback above.
        -->"""

        return note + "\n\n" + readme_content
