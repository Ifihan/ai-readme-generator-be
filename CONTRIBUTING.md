# Contributing to AI README Generator

Thank you for your interest in contributing to AI README Generator! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Security Vulnerabilities](#security-vulnerabilities)

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to victoriaolusheye@gmail.com.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-readme-generator-be.git
   cd ai-readme-generator-be
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/Ifihan/ai-readme-generator-be.git
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip and virtualenv
- Git
- MongoDB (local or cloud instance)
- A Google Gemini API key ([get one here](https://aistudio.google.com/api-keys))

### Installation

1. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file and add your configuration:

   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `MONGODB_URI`: Your MongoDB connection string
   - Other configuration variables as needed

4. **Run the application**:

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Project Structure

```
ai-readme-generator-be/
├── app/
│   ├── api/             # API route handlers
│   ├── core/            # Core functionality (auth, security, session)
│   ├── db/              # Database connection and utilities
│   ├── models/          # Database models (User, README entries)
│   ├── schemas/         # Pydantic schemas for validation
│   ├── services/        # Business logic (AI generation, repository analysis)
│   ├── utils/           # Helper functions and utilities
│   ├── middlewares/     # Request/response middlewares
│   ├── config.py        # Application configuration
│   ├── exceptions.py    # Custom exceptions
│   └── main.py          # FastAPI application entry point
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── Dockerfile          # Docker configuration
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes**: Help us squash bugs
- **New features**: Add new functionality for README generation
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Code quality**: Refactor code, improve performance
- **Security**: Report or fix security issues
- **AI Improvements**: Enhance README generation quality

### Finding Issues to Work On

- Check the [Issues](https://github.com/Ifihan/ai-readme-generator-be/issues) page
- Look for issues labeled `good first issue` for beginner-friendly tasks
- Issues labeled `help wanted` are open for anyone to work on
- Comment on an issue to let others know you're working on it

## Coding Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused (single responsibility)
- Use type hints where appropriate
- Use async/await for asynchronous operations

Example:

```python
async def generate_readme(repository_url: str, user_id: str) -> dict:
    """
    Generate a README for the given repository.

    Args:
        repository_url: The URL of the GitHub repository
        user_id: The ID of the user making the request

    Returns:
        Dictionary containing the generated README content and metadata

    Raises:
        RepositoryValidationError: If the repository URL is invalid
        AIGenerationError: If README generation fails
    """
    # Implementation here
```

### API Design

- Follow RESTful conventions
- Use appropriate HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Return meaningful HTTP status codes
- Include proper error messages in responses
- Use Pydantic schemas for request/response validation
- Document endpoints with clear descriptions

### Security Best Practices

- **Never** expose sensitive data (API keys, passwords, database credentials)
- Validate and sanitize all user input
- Use parameterized queries to prevent SQL/NoSQL injection
- Implement proper authentication and authorization
- Rate limit API endpoints to prevent abuse
- Log security-relevant events server-side only
- Never expose stack traces to users (log them server-side instead)
- Properly validate repository URLs to prevent SSRF attacks
- Use environment variables for configuration
- Hash and salt passwords using bcrypt or similar

## Commit Guidelines

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `security`: Security fixes or improvements

**Examples:**

```bash
feat(api): add endpoint for batch README generation

fix(services): handle timeout errors for large repositories

docs(readme): update installation instructions

security(auth): implement rate limiting on authentication endpoints

test(services): add unit tests for markdown generation
```

### Co-Authoring

When pairing or using AI assistance, add co-authors:

```
feat(ai): improve README structure generation

Co-Authored-By: Partner Name <partner@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Pull Request Process

### Before Submitting

1. **Test your changes thoroughly**

   - Run the test suite: `pytest`
   - Manually test the functionality
   - Ensure existing features still work
   - Test edge cases

2. **Update documentation**

   - Update README.md if needed
   - Add/update code comments and docstrings
   - Update API documentation

3. **Keep commits clean**
   - Use meaningful commit messages
   - Squash trivial commits if needed
   - Rebase on latest main branch

### Submitting a Pull Request

1. **Push your branch** to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub

   When you create a PR, a template will automatically be provided with sections for:

   - Description of changes
   - Type of change (bug fix, feature, etc.)
   - Related issues
   - Testing details
   - Screenshots (if applicable)
   - Checklist of requirements

   Fill out all relevant sections to help reviewers understand your changes.

3. **Respond to feedback**
   - Address review comments promptly
   - Push additional commits to your branch
   - Request re-review when ready

### Review Process

- At least one maintainer approval is required
- All CI checks must pass
- Code coverage should not decrease significantly
- Constructive feedback is always welcome
- Be patient - reviews may take a few days

## Reporting Bugs

### Before Reporting

- Check if the bug has already been reported
- Try to reproduce the bug with the latest version
- Collect relevant information (error messages, logs, etc.)

### Creating a Bug Report

When you're ready to report a bug, [create a new issue](https://github.com/Ifihan/ai-readme-generator-be/issues/new/choose) and select the **Bug Report** template. The template will guide you through providing all the necessary information.

## Suggesting Features

We love feature suggestions! [Create a new issue](https://github.com/Ifihan/ai-readme-generator-be/issues/new/choose) and select the **Feature Request** template. The template will help you provide all the details we need to evaluate and implement your idea.

## Security Vulnerabilities

**Do not** report security vulnerabilities through public GitHub issues.

Please report security issues privately to: victoriaolusheye@gmail.com

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond as quickly as possible and work with you to address the issue.

## Development Tips

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run with verbose output
pytest -v
```

### Running in Development Mode

The application uses FastAPI's auto-reload feature:

```bash
uvicorn app.main:app --reload
```

### Database Migrations

When making database schema changes:

1. Update the model in `app/models/`
2. Update corresponding schemas in `app/schemas/`
3. Test thoroughly with both new and existing data
4. Document the changes

### Working with the AI Service

- Test with various repository types and sizes
- Check prompt engineering changes carefully
- Monitor API usage and costs
- Consider adding caching for repeated requests

### API Testing

Use tools like:

- [Postman](https://www.postman.com/) or [Insomnia](https://insomnia.rest/) for manual testing
- FastAPI's automatic documentation at `http://localhost:8000/docs`
- `pytest` for automated testing

## Questions?

If you have questions:

- Check existing [Issues](https://github.com/Ifihan/ai-readme-generator-be/issues) and [Pull Requests](https://github.com/Ifihan/ai-readme-generator-be/pulls)
- Create a new issue with the `question` label
- Reach out to the maintainers

## Recognition

Contributors will be recognized in:

- GitHub contributors page
- Release notes (for significant contributions)
- README acknowledgments

Thank you for contributing to AI README Generator! 🎉
