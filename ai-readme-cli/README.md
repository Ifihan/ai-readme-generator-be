# ai-readme-cli
An AI-powered command-line interface (CLI) for automatically generating README.md files.

[
![PyPI Version](https://img.shields.io/pypi/v/ai-readme-cli.svg)
](https://pypi.org/project/ai-readme-cli/) [
![Build Status](https://img.shields.io/github/actions/workflow/status/user/ai-readme-cli/ci.yml)
](https://github.com/user/ai-readme-cli/actions) [
![Python Versions](https://img.shields.io/pypi/pyversions/ai-readme-cli.svg)
](https://pypi.org/project/ai-readme-cli/) [
![License](https://img.shields.io/pypi/l/ai-readme-cli.svg)
](https://pypi.org/project/ai-readme-cli/)

## Introduction

ai-readme-cli is a command-line interface (CLI) tool that generates project README files using an AI model. It addresses the challenge of manually creating comprehensive and well-structured documentation, which is often a time-consuming and neglected part of the development cycle.

This tool streamlines the documentation process by automating the initial draft, ensuring a consistent and professional format. Key benefits include a significant reduction in the time required to write documentation and the ability to produce a high-quality, structured README with minimal manual input.

## Features

*   **Automated Content Generation**:
    *   Generate a complete `README.md` by analyzing your local project repository.
    *   Create individual sections on demand, such as Installation, Usage, or Contributing.
*   **Intelligent Project Analysis**:
    *   Automatically detects the primary programming language and key frameworks.
    *   Identifies project dependencies from standard manifest files (e.g., `requirements.txt`, `package.json`).
*   **Flexible Interaction Modes**:
    *   Use interactive prompts to guide you through the README creation process.
    *   Run non-interactively with command-line flags for automated workflows.
*   **Customizable Output**:
    *   Choose which sections to include in the final generated file.
    *   Write content directly to `README.md` or pipe it to standard output.

## Installation

1.  Clone the repository.

    ```bash
    git clone https://github.com/user/ai-readme-cli.git
    ```

2.  Navigate to the project directory.

    ```bash
    cd ai-readme-cli
    ```

3.  Create a Python virtual environment.

    ```bash
    python -m venv venv
    ```

4.  Activate the virtual environment.

    *   **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *   **On Windows (PowerShell):**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```

5.  Install the required dependencies.

    ```bash
    pip install -r requirements.txt
    ```

6.  Create the environment variables file by copying the example.

    ```bash
    cp .env.example .env
    ```

7.  Modify the new `.env` file to include your API key.

    ```ini
    # .env
    OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ```

## Usage

Before running the tool, ensure your Google Gemini API key is configured. The recommended method is to set it as an environment variable.

```sh
export GOOGLE_API_KEY="your-api-key-here"
```

### Interactive Generation

To generate a README for the project in your current working directory, run the tool without any arguments. This will initiate an interactive session where you will be prompted to provide or confirm project details.

```sh
ai-readme-cli
```

The tool will analyze your project structure and guide you through a series of questions to gather the necessary information for generating a comprehensive README.md file.

### Generating for a Specific Directory

You can generate a README for a project located in a different directory by providing the path as an argument. This is useful for running the generator from a central location or in automated scripts.

```sh
ai-readme-cli /path/to/your/project
```

### Passing the API Key as an Argument

As an alternative to using an environment variable, you can pass the API key directly using the `--api-key` flag. This method is suitable for environments where setting environment variables is not feasible.

```sh
ai-readme-cli --api-key "your-api-key-here"
```

## Contributing

Contributions are welcome. To contribute, please fork the repository, make the changes, and submit a pull request for review. For significant architectural changes, open an issue first to discuss the proposed implementation.

### Bug Reports and Feature Requests

Use the GitHub Issues tracker to report bugs or request new features. Provide a clear title and a detailed description. For bug reports, include the following:

-   Steps to reproduce the issue.
-   Expected behavior and the actual result.
-   Relevant configuration or error logs.

### Development Environment Setup

To set up a local development environment, ensure you have Python 3.8+ installed.

1.  Fork and clone the repository:
    ```bash
    git clone https://github.com/Drex72/ai-readme-generator-be.git
    cd ai-readme-cli
    ```

2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install development dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Install the CLI in editable mode:
    ```bash
    pip install -e .
    ```

5.  Run the test suite to verify the setup:
    ```bash
    pytest
    ```

### Coding Standards

This project enforces strict coding standards to maintain code quality and consistency.

-   **Formatting**: Code is formatted using [Black](https://github.com/psf/black). Run `black .` before committing changes.
-   **Linting**: [Flake8](https://flake8.pycqa.org/en/latest/) is used for linting. Run `flake8 .` to check for style violations.
-   **Type Hinting**: All new functions and methods must include complete type hints.

Pull requests that do not pass formatting and linting checks will be rejected.

### Branching and Commits

Follow these conventions for branches and commit messages to ensure a clean and understandable project history.

**Branch Naming**

Create branches from the `main` branch. Use the following prefixes in your branch names:

-   `feature/`: For new features (e.g., `feature/add-json-output`).
-   `fix/`: For bug fixes (e.g., `fix/resolve-api-timeout`).
-   `docs/`: For documentation changes (e.g., `docs/update-contributing-guide`).

**Commit Messages**

Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. Each commit message should consist of a header, a body, and a footer.

Example:
```
feat: add support for custom templates

Allows users to specify a custom template path via the --template
flag, providing greater flexibility for README generation.

Resolves: #42
```

## License

All Rights Reserved.

This project is provided without an open-source license. The software is under exclusive copyright, and you may not use, copy, modify, or distribute it without explicit permission from the copyright holder.

## Tech Stack

[
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
](https://www.python.org)
[
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai&logoColor=white)
](https://openai.com/docs/api-reference)
[
![Typer](https://img.shields.io/badge/Typer-CLI-black?style=for-the-badge&logo=python&logoColor=white)
](https://typer.tiangolo.com/)

This project is built on Python and leverages several modern libraries for its command-line interface, AI integration, and development workflow.

### Core Application

-   **Python 3.10+:** The core programming language for the application.
-   **OpenAI Python Client:** Manages all API interactions with the OpenAI service.
-   **Typer:** Provides the foundation for the command-line interface, built on top of Click.
-   **Rich:** Used for creating beautiful and informative terminal output.
-   **Pydantic:** Handles data validation and strict type enforcement for configuration and API models.

### Development & Tooling

-   **Poetry:** Manages project dependencies, virtual environments, and packaging.
-   **Pytest:** The framework used for all unit and integration testing.
-   **Ruff:** Serves as an extremely fast linter and code formatter to ensure code quality and consistency.

## Prerequisites

To use this tool, your system must meet the following requirements.

### Required

*   **Python 3.8 or newer**: This project requires a modern version of Python. Verify your installation by running `python3 --version`.
*   **pip**: The Python package installer is required to install project dependencies. It is included with most Python distributions.
*   **AI Provider API Key**: You must have an active API key from a supported large language model provider (e.g., OpenAI, Anthropic, Google). This key must be configured as an environment variable. For OpenAI, set the following variable:
    ```sh
    export OPENAI_API_KEY="your-api-key-here"
    ```

### Recommended

*   **Python Virtual Environment**: It is highly recommended to use a virtual environment to isolate the project's dependencies from your system's global Python environment. You can use Python's built-in `venv` module.

## Configuration

The CLI can be configured via a TOML file or through environment variables. Environment variables take precedence over settings defined in the configuration file. The `api_key` is the only required setting.

### Configuration File

Create a configuration file at `~/.config/ai-readme-cli/config.toml` to persist your settings.

**Example `config.toml`:**

```toml
# API key for the AI service (e.g., OpenAI, Anthropic).
# This is a required setting.
api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# The specific large language model to use for generation.
model = "gpt-4o"

# The name of the generated output file.
output_file = "README.md"

# The creative temperature for the model (0.0 to 2.0).
# Lower values are more deterministic.
temperature = 0.7

# Request timeout in seconds.
timeout = 60
```

### Configuration Options

| Option        | Type    | Default       | Required | Description                                                  |
| :------------ | :------ | :------------ | :------- | :----------------------------------------------------------- |
| `api_key`     | string  | `None`        | **Yes**  | Your API key for the backing AI service.                     |
| `model`       | string  | `"gpt-4o"`    | No       | The identifier for the AI model to use for generation.       |
| `output_file` | string  | `"README.md"` | No       | The filename for the generated README file.                  |
| `template`    | string  | `None`        | No       | Path to a custom Jinja2 template file for the final output.  |
| `temperature` | float   | `0.7`         | No       | Controls model randomness. Must be between 0.0 and 2.0.      |
| `timeout`     | integer | `60`          | No       | The timeout in seconds for API requests.                     |

### Environment Variables

All configuration options can be set using environment variables. The variables must be prefixed with `AI_README_` followed by the option name in uppercase.

To set the API key and model, export the following variables in your shell:

```bash
# For bash, zsh, or similar shells
export AI_README_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AI_README_MODEL="gemini-1.5-pro"
```

## Testing

This project uses `pytest` for test execution and `pytest-cov` for code coverage analysis. Ensure you have installed the development dependencies before running tests.

```bash
pip install -r requirements-dev.txt
```

### Running All Tests

Execute the entire test suite from the root of the repository. This includes all unit and integration tests.

```bash
pytest
```

### Test Types

The test suite is organized into two primary categories:

*   **Unit Tests (`tests/unit`):** These tests verify the functionality of individual components in isolation, without external dependencies like file systems or network access.
*   **Integration Tests (`tests/integration`):** These tests validate the interactions between different components of the CLI to ensure they work together as expected.

### Running Specific Tests

Run a specific test file or a subset of tests using `pytest` arguments.

To run all tests within a specific file:

```bash
pytest tests/unit/test_parser.py
```

To run tests matching a specific name or keyword expression (`-k`):

```bash
pytest -k "test_generate_readme_with_template"
```

### Test Coverage

Generate a test coverage report to identify untested code. The results will be displayed in the terminal and a detailed HTML report will be generated in the `htmlcov/` directory.

```bash
pytest --cov=src --cov-report=term --cov-report=html
```

To view the HTML report, open `htmlcov/index.html` in your browser.

## Deployment

This project is a command-line interface (CLI) application. Deployment involves either publishing it as a package to the Python Package Index (PyPI) for public installation via `pip`, or containerizing it with Docker for isolated, portable execution.

### Environment Variables

The application requires an API key for the underlying AI service. Configure this key as an environment variable before running the application.

```shell
export AI_API_KEY="your-api-key-here"
```

### Option 1: Publishing to PyPI

Publishing to PyPI makes the CLI tool installable for any user with `pip`. This process requires `setuptools`, `wheel`, and `twine`.

1.  **Install Packaging Tools**
    Install or upgrade the necessary Python packaging libraries.

    ```shell
    python3 -m pip install --upgrade setuptools wheel twine
    ```

2.  **Generate Distribution Archives**
    Run the `setup.py` script to create the source archive and wheel in the `dist/` directory.

    ```shell
    python3 setup.py sdist bdist_wheel
    ```

3.  **Upload to PyPI**
    Use `twine` to upload the distribution packages. You will be prompted for your PyPI username and password.

    ```shell
    twine upload dist/*
    ```

For detailed guidance, refer to the official [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

### Option 2: Containerizing with Docker

Use Docker to create a self-contained image that includes the application and all its dependencies. A `Dockerfile` must be present in the project root.

1.  **Build the Docker Image**
    From the repository's root directory, build the Docker image using the `docker build` command.

    ```shell
    docker build -t ai-readme-cli .
    ```

2.  **Run the Docker Container**
    Execute the application within a new container. Pass the required API key using the `--env` or `-e` flag.

    ```shell
    docker run --rm -it -e AI_API_KEY="your-api-key-here" ai-readme-cli --help
    ```

    -   The `--rm` flag automatically removes the container when it exits.
    -   `-it` allocates a pseudo-TTY for interactive processes.

Consult the official [Docker run reference](https://docs.docker.com/engine/reference/commandline/run/) for additional container configuration options.