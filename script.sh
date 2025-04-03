#!/bin/bash

# Create the main project directory
mkdir -p readme_generator

# Create the app directory structure
mkdir -p readme_generator/app/{api/routes,core,services,schemas,utils}
mkdir -p readme_generator/tests/{test_api,test_services}

# Create __init__.py files to make directories Python packages
touch readme_generator/app/__init__.py
touch readme_generator/app/api/__init__.py
touch readme_generator/app/api/routes/__init__.py
touch readme_generator/app/core/__init__.py
touch readme_generator/app/services/__init__.py
touch readme_generator/app/schemas/__init__.py
touch readme_generator/app/utils/__init__.py
touch readme_generator/tests/__init__.py
touch readme_generator/tests/test_api/__init__.py
touch readme_generator/tests/test_services/__init__.py

# Create base files
touch readme_generator/app/main.py
touch readme_generator/app/config.py
touch readme_generator/app/dependencies.py
touch readme_generator/app/exceptions.py
touch readme_generator/app/api/deps.py

# Create route files
touch readme_generator/app/api/routes/auth.py
touch readme_generator/app/api/routes/repositories.py
touch readme_generator/app/api/routes/readme.py
touch readme_generator/app/api/routes/contributing.py

# Create core files
touch readme_generator/app/core/auth.py
touch readme_generator/app/core/security.py
touch readme_generator/app/core/session.py

# Create service files
touch readme_generator/app/services/github_service.py
touch readme_generator/app/services/gemini_service.py

# Create schema files
touch readme_generator/app/schemas/auth.py
touch readme_generator/app/schemas/repository.py
touch readme_generator/app/schemas/readme.py
touch readme_generator/app/schemas/contributing.py

# Create utility files
touch readme_generator/app/utils/markdown_utils.py

# Create test files
touch readme_generator/tests/conftest.py
touch readme_generator/tests/test_api/test_auth.py
touch readme_generator/tests/test_api/test_repositories.py
touch readme_generator/tests/test_api/test_readme.py
touch readme_generator/tests/test_api/test_contributing.py
touch readme_generator/tests/test_services/test_github_service.py
touch readme_generator/tests/test_services/test_gemini_service.py

# Create project files
touch readme_generator/.env.example
touch readme_generator/.gitignore
touch readme_generator/pyproject.toml
touch readme_generator/README.md
touch readme_generator/requirements.txt

echo "Project structure created successfully!"