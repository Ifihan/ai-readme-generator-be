import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import git
from git import InvalidGitRepositoryError

class LocalRepositoryService:
    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path).resolve()

    def analyze_repository(self) -> Dict[str, Any]:
        """Analyze the local repository and return detailed information."""
        # Get basic repository info
        package_info = self._get_package_info()
        languages = self._detect_languages()
        primary_language = self._detect_primary_language(languages)
        file_structure = self._get_file_structure()
        code_samples = self._get_code_samples(primary_language)

        # Try to get git info
        git_info = self._get_git_info()

        repo_name = (
            package_info.get('name') or
            git_info.get('repo') or
            self.repository_path.name
        )

        return {
            'name': repo_name,
            'description': package_info.get('description'),
            'language': primary_language,
            'languages': languages,
            'topics': package_info.get('keywords', []),
            'homepage': package_info.get('homepage'),
            'clone_url': git_info.get('clone_url'),
            'license': self._detect_license(),
            'license_file': self._find_license_file(),
            'file_structure': file_structure,
            'code_samples': code_samples
        }

    def _get_package_info(self) -> Dict[str, Any]:
        """Get package information from various configuration files."""
        # Try package.json first
        package_json_path = self.repository_path / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Try pyproject.toml
        pyproject_path = self.repository_path / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                # Try to use tomli/tomllib (Python 3.11+) or fall back to manual parsing
                try:
                    import tomllib
                    with open(pyproject_path, 'rb') as f:
                        data = tomllib.load(f)
                except ImportError:
                    try:
                        import tomli
                        with open(pyproject_path, 'rb') as f:
                            data = tomli.load(f)
                    except ImportError:
                        # Manual TOML parsing for basic cases
                        with open(pyproject_path) as f:
                            content = f.read()
                            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
                            desc_match = re.search(r'description\s*=\s*"([^"]+)"', content)
                            return {
                                'name': name_match.group(1) if name_match else None,
                                'description': desc_match.group(1) if desc_match else None
                            }

                tool_poetry = data.get('tool', {}).get('poetry', {})
                project = data.get('project', {})
                return {
                    'name': tool_poetry.get('name') or project.get('name'),
                    'description': tool_poetry.get('description') or project.get('description'),
                    'keywords': tool_poetry.get('keywords') or project.get('keywords', []),
                    'homepage': tool_poetry.get('homepage') or project.get('urls', {}).get('homepage')
                }
            except Exception:
                pass

        # Try setup.py (basic parsing)
        setup_py_path = self.repository_path / 'setup.py'
        if setup_py_path.exists():
            try:
                with open(setup_py_path) as f:
                    content = f.read()
                    name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
                    return {
                        'name': name_match.group(1) if name_match else None,
                        'description': desc_match.group(1) if desc_match else None
                    }
            except IOError:
                pass

        # Try Cargo.toml
        cargo_path = self.repository_path / 'Cargo.toml'
        if cargo_path.exists():
            try:
                # Try TOML parsing or manual parsing
                try:
                    import tomllib
                    with open(cargo_path, 'rb') as f:
                        data = tomllib.load(f)
                except ImportError:
                    try:
                        import tomli
                        with open(cargo_path, 'rb') as f:
                            data = tomli.load(f)
                    except ImportError:
                        # Manual parsing
                        with open(cargo_path) as f:
                            content = f.read()
                            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
                            desc_match = re.search(r'description\s*=\s*"([^"]+)"', content)
                            return {
                                'name': name_match.group(1) if name_match else None,
                                'description': desc_match.group(1) if desc_match else None
                            }

                package = data.get('package', {})
                return {
                    'name': package.get('name'),
                    'description': package.get('description'),
                    'keywords': package.get('keywords', []),
                    'homepage': package.get('homepage')
                }
            except Exception:
                pass

        # Try go.mod
        go_mod_path = self.repository_path / 'go.mod'
        if go_mod_path.exists():
            try:
                with open(go_mod_path) as f:
                    content = f.read()
                    module_match = re.search(r'^module\s+(.+)$', content, re.MULTILINE)
                    if module_match:
                        return {
                            'name': Path(module_match.group(1)).name
                        }
            except IOError:
                pass

        return {}

    def _detect_languages(self) -> Dict[str, int]:
        """Detect programming languages used in the repository."""
        languages = {}
        extensions = {
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.py': 'Python',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C',
            '.hpp': 'C++',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.kt': 'Kotlin',
            '.swift': 'Swift',
            '.scala': 'Scala',
            '.sh': 'Shell',
            '.ps1': 'PowerShell',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'Less',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.dart': 'Dart',
            '.lua': 'Lua',
            '.r': 'R',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            '.sql': 'SQL'
        }

        ignore_dirs = {
            'node_modules', '.git', 'dist', 'build', '.next',
            '__pycache__', 'target', '.cargo', 'vendor'
        }

        for root, dirs, files in os.walk(self.repository_path):
            # Remove ignored directories from dirs to prevent walking into them
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                ext = Path(file).suffix.lower()
                language = extensions.get(ext)
                if language:
                    file_path = Path(root) / file
                    try:
                        file_size = file_path.stat().st_size
                        languages[language] = languages.get(language, 0) + file_size
                    except OSError:
                        pass

        return languages

    def _detect_primary_language(self, languages: Dict[str, int]) -> str:
        """Detect the primary programming language."""
        if not languages:
            return 'Unknown'

        return max(languages.items(), key=lambda x: x[1])[0]

    def _get_file_structure(self, max_depth: int = 2) -> str:
        """Get the file structure of the repository."""
        structure = []
        ignore_dirs = {
            'node_modules', '.git', 'dist', 'build', '.next',
            '__pycache__', 'target', '.cargo', 'vendor'
        }

        def add_to_structure(path: Path, prefix: str = "", depth: int = 0):
            if depth >= max_depth:
                return

            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            except PermissionError:
                return

            for i, item in enumerate(items):
                if item.name.startswith('.') and item.name not in {'.env.example', '.gitignore'}:
                    continue
                if item.name in ignore_dirs:
                    continue

                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "

                if item.is_dir():
                    structure.append(f"{prefix}{connector}{item.name}/")
                    if depth + 1 < max_depth:
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        add_to_structure(item, new_prefix, depth + 1)
                else:
                    structure.append(f"{prefix}{connector}{item.name}")

        add_to_structure(self.repository_path)
        return '\n'.join(structure) if structure else 'No files found'

    def _get_code_samples(self, primary_language: str) -> Dict[str, str]:
        """Get representative code samples from the repository."""
        samples = {}

        # Important files to look for
        important_files = [
            'README.md', 'package.json', 'pyproject.toml', 'requirements.txt',
            'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle'
        ]

        # Language-specific entry points
        entry_points = {
            'JavaScript': ['index.js', 'app.js', 'main.js', 'src/index.js'],
            'TypeScript': ['index.ts', 'app.ts', 'main.ts', 'src/index.ts'],
            'Python': ['main.py', 'app.py', '__init__.py', 'setup.py'],
            'Java': ['Main.java', 'App.java'],
            'Go': ['main.go'],
            'Rust': ['main.rs', 'lib.rs'],
            'C++': ['main.cpp', 'main.cc'],
            'C': ['main.c'],
            'Ruby': ['app.rb', 'main.rb'],
            'PHP': ['index.php', 'app.php']
        }

        files_to_check = important_files + entry_points.get(primary_language, [])

        for file_name in files_to_check:
            file_path = self.repository_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
                        # Limit content to first 1000 characters
                        samples[file_name] = content[:1000]
                except (UnicodeDecodeError, IOError):
                    # Skip files that can't be read
                    pass

        return samples

    def _detect_license(self) -> Optional[str]:
        """Detect the license of the repository."""
        # Check package.json first
        package_json_path = self.repository_path / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path) as f:
                    data = json.load(f)
                    license_info = data.get('license')
                    if license_info:
                        return license_info
            except (json.JSONDecodeError, IOError):
                pass

        # Check license file
        license_file = self._find_license_file()
        if license_file:
            try:
                with open(self.repository_path / license_file, encoding='utf-8') as f:
                    content = f.read().upper()

                    if 'MIT' in content:
                        return 'MIT'
                    elif 'APACHE' in content:
                        return 'Apache 2.0'
                    elif 'GPL' in content:
                        return 'GPL'
                    elif 'BSD' in content:
                        return 'BSD'
                    elif 'ISC' in content:
                        return 'ISC'

                    return 'Custom'
            except (UnicodeDecodeError, IOError):
                pass

        return None

    def _find_license_file(self) -> Optional[str]:
        """Find a license file in the repository."""
        license_files = [
            'LICENSE', 'LICENSE.md', 'LICENSE.txt',
            'License', 'License.md', 'License.txt',
            'license', 'license.md', 'license.txt'
        ]

        for license_file in license_files:
            if (self.repository_path / license_file).exists():
                return license_file

        return None

    def _get_git_info(self) -> Dict[str, Any]:
        """Get git repository information."""
        try:
            repo = git.Repo(self.repository_path)

            # Get origin URL
            try:
                origin_url = repo.remotes.origin.url
                return self._parse_git_url(origin_url)
            except AttributeError:
                # No origin remote
                pass

        except InvalidGitRepositoryError:
            # Not a git repository
            pass

        return {}

    def _parse_git_url(self, url: str) -> Dict[str, Any]:
        """Parse a git URL to extract repository information."""
        if not url:
            return {}

        # Handle SSH URLs
        if url.startswith('git@'):
            match = re.match(r'git@github\.com:(.+)/(.+)\.git$', url)
            if match:
                owner, repo = match.groups()
                return {
                    'repo': repo,
                    'clone_url': f'https://github.com/{owner}/{repo}.git'
                }

        # Handle HTTPS URLs
        if 'github.com' in url:
            match = re.search(r'github\.com/(.+)/(.+?)(?:\.git)?/?$', url)
            if match:
                owner, repo = match.groups()
                repo = repo.rstrip('.git')
                return {
                    'repo': repo,
                    'clone_url': f'https://github.com/{owner}/{repo}.git'
                }

        return {'clone_url': url}

    def check_existing_readme(self) -> Optional[Dict[str, Any]]:
        """Check for existing README file."""
        readme_files = [
            'README.md', 'README.rst', 'README.txt', 'README',
            'readme.md', 'readme.rst', 'readme.txt', 'readme'
        ]

        for readme_file in readme_files:
            file_path = self.repository_path / readme_file
            if file_path.exists():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    return {
                        'path': str(file_path),
                        'content': content,
                        'size': len(content)
                    }
                except (UnicodeDecodeError, IOError):
                    continue

        return None