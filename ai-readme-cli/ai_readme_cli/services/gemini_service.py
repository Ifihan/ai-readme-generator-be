from typing import Dict, List, Any
import google.generativeai as genai
from ..utils.readme_prompts import ReadmePrompts

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.prompts = ReadmePrompts()

    def generate_readme(self, repo_info: Dict[str, Any], sections: List[Dict[str, Any]], existing_readme: str = None) -> Dict[str, Any]:
        """Generate or optimize a README for the repository."""
        try:
            # Check for existing README first
            if existing_readme and existing_readme.strip():
                print("Found existing README - will optimize it instead of creating from scratch")

                # Create improvement instructions based on requested sections
                section_names = [section['name'] for section in sections]
                improvement_feedback = f"""
                Please improve this existing README by enhancing or adding the following sections: {', '.join(section_names)}.

                Repository Information:
                - Name: {repo_info.get('name', 'Unknown')}
                - Description: {repo_info.get('description', 'No description provided')}
                - Primary Language: {repo_info.get('language', 'Not specified')}
                - Clone URL: {repo_info.get('clone_url', 'Local repository')}

                Guidelines:
                - Keep good existing content but enhance it
                - Add missing sections from the requested list
                - Improve existing sections to be more comprehensive and professional
                - Use the repository information above for accuracy
                - Follow modern README best practices
                """

                optimized_content = self.refine_readme(existing_readme, improvement_feedback)
                return {
                    'content': optimized_content,
                    'sections_generated': section_names,
                    'optimization': True
                }

            # Sort sections by order
            sorted_sections = sorted(sections, key=lambda x: x['order'])

            # Generate header first
            header_content = self._generate_header(repo_info)

            # Generate each section
            section_contents = []
            sections_generated = []

            for section in sorted_sections:
                try:
                    section_content = self._generate_section(section, repo_info, sections)
                    section_contents.append(section_content)
                    sections_generated.append(section['name'])
                except Exception as e:
                    print(f"Warning: Failed to generate section {section['name']}: {e}")
                    section_contents.append(f"## {section['name']}\n\n*Content generation failed for this section.*")
                    sections_generated.append(section['name'])

            full_content = '\n\n'.join([header_content] + section_contents)

            return {
                'content': full_content,
                'sections_generated': sections_generated,
                'optimization': False
            }

        except Exception as e:
            raise Exception(f"README generation failed: {str(e)}")

    def _generate_header(self, repo_info: Dict[str, Any]) -> str:
        """Generate the header section of the README."""
        prompt = self.prompts.get_header_prompt(repo_info)
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _generate_section(
        self,
        section: Dict[str, Any],
        repo_info: Dict[str, Any],
        all_sections: List[Dict[str, Any]]
    ) -> str:
        """Generate a specific section of the README."""
        prompt = self.prompts.get_section_specific_prompt(section, repo_info, all_sections)

        if (section['name'].lower() in ['usage', 'examples', 'getting started'] and
            repo_info.get('code_samples')):
            code_context = '\n\nCode Samples for Reference:\n'
            for file_path, content in repo_info['code_samples'].items():
                code_context += f'\nFile: {file_path}\n```\n{content[:500]}...\n```\n'
            prompt += code_context

        response = self.model.generate_content(prompt)
        return response.text.strip()

    def refine_readme(self, content: str, feedback: str) -> str:
        """Refine an existing README based on user feedback."""
        prompt = f"""
You are an expert technical writer specializing in improving README documentation.

Below is a README.md file that needs to be refined based on user feedback:

```markdown
{content}
```

User feedback:
{feedback}

Please revise the README to address this feedback while maintaining professional quality, proper Markdown formatting, and comprehensive coverage of the project.

Respond with ONLY the revised README.md content in Markdown format, without any additional explanation or conversation.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"README refinement failed: {str(e)}")