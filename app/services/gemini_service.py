from typing import List, Dict, Any, Optional
import logging
import os
import re
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.schemas.readme import ReadmeSection, ReadmeGenerationRequest
from app.services.github_service import GitHubService
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

    def _create_readme_prompt(
        self, repo_info: Dict[str, Any], sections: List[ReadmeSection]
    ) -> str:
        """Create a prompt for README generation based on repository information and requested sections."""
        # Format sections for the prompt
        section_descriptions = "\n".join(
            [f"- {section.name}: {section.description}" for section in sections]
        )

        # Add file structure and code samples if available
        file_structure = repo_info.get("file_structure", "Not provided")
        code_samples = ""

        if "code_samples" in repo_info:
            code_samples = "\nCode Samples:\n"
            for file_path, content in repo_info["code_samples"].items():
                # Limit content size to avoid token limits
                # Escape curly braces in code content by doubling them
                sample_content = (
                    content[:500] + "..." if len(content) > 500 else content
                )
                sample_content = sample_content.replace("{", "{{").replace("}", "}}")
                code_samples += f"\nFile: {file_path}\n```\n{sample_content}\n```\n"

        # Base prompt template
        prompt = f"""
        # TASK
        You are an expert technical writer specializing in creating clear, professional, and comprehensive README documentation for software projects.
        
        Create a README.md for a GitHub repository with the following information:
        
        # REPOSITORY INFORMATION
        - Name: {repo_info.get('name', 'Unknown')}
        - Description: {repo_info.get('description', 'No description provided')}
        - Primary Language: {repo_info.get('language', 'Not specified')}
        - Topics/Tags: {', '.join(repo_info.get('topics', ['None']))}
        
        # FILE STRUCTURE
        {file_structure}
        
        {code_samples}
        
        # REQUIRED SECTIONS
        The README should contain the following sections:
        {section_descriptions}
        
        # GUIDELINES
        1. Use professional, clear, and concise language
        2. Follow Markdown best practices with proper headings, lists, code blocks, etc.
        3. Make the README comprehensive but not overly verbose
        4. Include relevant badges where appropriate
        5. For installation and usage sections, use real commands based on the repo's language/framework
        6. Provide concrete examples where possible
        7. Format the output as a valid Markdown document
        8. Do not include sections that are not requested
        
        # OUTPUT FORMAT
        Respond with ONLY the README.md content in Markdown format, without any additional explanation or conversation.
        """

        return prompt

    async def generate_readme(
        self, request: ReadmeGenerationRequest, github_service: GitHubService
    ) -> str:
        """Generate a README for a GitHub repository with automatic fallback handling."""
        # Get repository information
        repo_info = await github_service.get_repository_details(request.repository_url)

        # Get file structure if needed
        if any(
            section.name.lower()
            in ["project structure", "file structure", "organization"]
            for section in request.sections
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

        # First attempt: Try with default token limit
        try:
            return await self._generate_readme_full(repo_info, request.sections)
        except Exception as e:
            logger.warning(
                f"Initial README generation failed: {str(e)}. Trying with increased token limit..."
            )

            # Second attempt: Try with increased token limit
            try:
                # Create a higher-capacity model
                original_llm = self.llm
                self.llm = self._create_llm(self.max_fallback_tokens)

                result = await self._generate_readme_full(repo_info, request.sections)

                # Restore original model
                self.llm = original_llm
                return result
            except Exception as e2:
                logger.warning(
                    f"Increased token limit attempt failed: {str(e2)}. Falling back to section-by-section generation..."
                )

                # Third attempt: Section-by-section generation
                # Restore original model if needed
                self.llm = original_llm
                return await self._generate_readme_by_section(
                    repo_info, request.sections
                )

    async def _generate_readme_full(
        self, repo_info: Dict[str, Any], sections: List[ReadmeSection]
    ) -> str:
        """Generate a complete README in one call."""
        # Create prompt for README generation
        prompt = self._create_readme_prompt(repo_info, sections)

        # Create chain with prompt template
        prompt_template = ChatPromptTemplate.from_template(prompt)
        chain = prompt_template | self.llm | StrOutputParser()

        # Generate README content
        readme_content = await chain.ainvoke({})

        # Check for potential truncation
        if self._check_for_truncation(readme_content, sections):
            logger.warning("Potential truncation detected in README generation")
            raise ValueError("Potential truncation detected")

        return readme_content

    async def _generate_readme_by_section(
        self, repo_info: Dict[str, Any], sections: List[ReadmeSection]
    ) -> str:
        """Generate README content section by section."""
        # Start with the header section (title, badges, short description)
        header_prompt = f"""
        Create only the header section of a README.md for the GitHub repository: {repo_info.get('name')}
        
        Repository Information:
        - Name: {repo_info.get('name', 'Unknown')}
        - Description: {repo_info.get('description', 'No description provided')}
        - Primary Language: {repo_info.get('language', 'Not specified')}
        
        Include:
        1. A title (H1 heading with the repository name)
        2. A brief one-paragraph description of what the project does
        3. Appropriate badges if needed (build status, version, license, etc.)
        
        Format the output as Markdown. ONLY include the header section, no other sections.
        """

        header_prompt_template = ChatPromptTemplate.from_template(header_prompt)
        header_chain = header_prompt_template | self.llm | StrOutputParser()
        header_content = await header_chain.ainvoke({})

        # Generate each section separately
        sections_content = []
        for section in sorted(sections, key=lambda x: x.order):
            section_prompt = f"""
            Create ONLY the "{section.name}" section of a README.md for a GitHub repository.
            
            Repository Information:
            - Name: {repo_info.get('name', 'Unknown')}
            - Description: {repo_info.get('description', 'No description provided')}
            - Primary Language: {repo_info.get('language', 'Not specified')}
            - Topics/Tags: {', '.join(repo_info.get('topics', ['None']))}
            
            Section Details:
            - Section Name: {section.name}
            - Section Description: {section.description}
            
            Additional Context:
            """

            # Add relevant context based on section type
            if section.name.lower() in [
                "project structure",
                "file structure",
                "organization",
            ]:
                section_prompt += f"\nFile Structure:\n{repo_info.get('file_structure', 'Not available')}\n"

            if section.name.lower() in ["usage", "examples", "getting started"]:
                sample_files = repo_info.get("code_samples", {})
                section_prompt += "\nCode Samples:\n"
                for file_path, content in sample_files.items():
                    # Escape curly braces in code content by doubling them
                    escaped_content = (
                        content[:500].replace("{", "{{").replace("}", "}}")
                    )
                    section_prompt += (
                        f"\nFile: {file_path}\n```\n{escaped_content}...\n```\n"
                    )

            section_prompt += """
            Format the output as Markdown. Start with a level-2 heading (##) for the section name.
            ONLY include this specific section, do not include any other sections.
            """

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
        return full_content

    def _check_for_truncation(
        self, content: str, sections: List[ReadmeSection]
    ) -> bool:
        """Check if the generated content appears to be truncated."""
        # Check for common truncation indicators
        truncation_indicators = [
            content.endswith("..."),
            content.endswith("…"),
            content.endswith("to be continued"),
            content.endswith("continued"),
        ]

        if any(truncation_indicators):
            return True

        # Check if all expected sections are present
        required_section_names = [
            section.name for section in sections if section.required
        ]

        # Extract section headings from content using regex
        section_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)
        found_sections = section_pattern.findall(content)

        # Check if all required sections are present
        for required_section in required_section_names:
            if not any(
                required_section.lower() in found.lower() for found in found_sections
            ):
                return True

        return False

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

    async def analyze_repository_for_readme(
        self,
        repo_info: Dict[str, Any],
        repo_files: List[Dict[str, Any]],
        key_files_content: Dict[str, str],
    ) -> Dict[str, Any]:
        """Analyze a repository to determine the best README structure."""
        try:
            # Create context for the analysis prompt
            file_structure = self._format_file_structure(repo_files)
            key_files_summary = self._summarize_key_files(key_files_content)

            context = {
                "repo_name": repo_info.get("name", ""),
                "repo_description": repo_info.get(
                    "description", "No description provided"
                ),
                "file_structure": file_structure,
                "key_files_summary": key_files_summary,
                "programming_language": repo_info.get("language", "Not specified"),
            }

            # Create the analysis prompt
            prompt = f"""
            You are an expert at analyzing GitHub repositories and determining the best structure for README documentation.
            
            # REPOSITORY INFORMATION
            - Name: {context['repo_name']}
            - Description: {context['repo_description']}
            - Programming Language: {context['programming_language']}
            
            # FILE STRUCTURE
            {context['file_structure']}
            
            # KEY FILES SUMMARY
            {context['key_files_summary']}
            
            # TASK
            Analyze this repository and determine the most appropriate sections for a comprehensive README.md file.
            
            ## ANALYSIS GUIDELINES
            1. Consider the programming language and common documentation practices for that ecosystem
            2. Look at the file structure to understand project organization and components
            3. Consider the purpose of the repository (library, application, framework, etc.)
            4. Identify sections that would be most useful for users of this project
            
            # OUTPUT FORMAT
            Provide your analysis in this format:
            
            ## Recommended Sections:
            - section_id_1: Section Title 1
            - section_id_2: Section Title 2
            (etc.)
            
            ## Custom Sections:
            - Additional Section Title 1
            - Additional Section Title 2
            (etc.)
            
            ## Analysis:
            Brief explanation of why these sections are recommended for this repository.
            """

            # Create the analysis chain
            prompt_template = ChatPromptTemplate.from_template(prompt)
            chain = prompt_template | self.llm | StrOutputParser()

            # Execute the chain to analyze the repository
            response = await chain.ainvoke({})

            # Extract recommended sections
            recommended_sections = []
            custom_sections = []

            # Parse the response to extract recommended sections
            lines = response.strip().split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if line.startswith("## Recommended Sections:"):
                    current_section = "recommended"
                elif line.startswith("## Custom Sections:"):
                    current_section = "custom"
                elif line.startswith("## Analysis:"):
                    current_section = "analysis"
                elif line.startswith("- ") and current_section == "recommended":
                    section = line[2:].strip()
                    if ":" in section:
                        section_id, section_name = section.split(":", 1)
                        recommended_sections.append(
                            {
                                "id": section_id.strip(),
                                "name": section_name.strip(),
                            }
                        )
                elif line.startswith("- ") and current_section == "custom":
                    section = line[2:].strip()
                    custom_sections.append(section)

            return {
                "recommended_sections": recommended_sections,
                "custom_sections": custom_sections,
                "analysis": response,
            }

        except Exception as e:
            logger.error(f"Failed to analyze repository: {str(e)}")
            raise GeminiApiException(detail=f"Failed to analyze repository: {str(e)}")

    def _format_file_structure(self, files: List[Dict[str, Any]]) -> str:
        """Format the file structure for inclusion in the prompt."""
        if not files:
            return "No files available"

        # Create a formatted string representation of the file structure
        file_list = []
        for file in files:
            file_path = file.get("path", "")
            file_type = file.get("type", "")
            file_size = file.get("size", 0)

            if file_type == "dir":
                file_list.append(f"Directory: {file_path}")
            else:
                file_list.append(f"File: {file_path} ({file_size} bytes)")

        return "\n".join(file_list)

    def _summarize_key_files(self, key_files: Dict[str, str]) -> str:
        """Summarize key files content for inclusion in the prompt."""
        if not key_files:
            return "No key files available"

        # Create a summary of key files
        summary_parts = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)

        for file_key, content in key_files.items():
            if not content:
                continue

            # For large files, just include the first chunk
            chunks = text_splitter.split_text(content)
            if chunks:
                summary_parts.append(f"### {file_key.upper()} FILE")
                summary_parts.append(chunks[0])
                if len(chunks) > 1:
                    summary_parts.append("(content truncated for brevity)")

        if not summary_parts:
            return "No key file content available"

        return "\n\n".join(summary_parts)
