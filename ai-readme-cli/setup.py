from setuptools import setup, find_packages

setup(
    name="ai-readme-cli",
    version="1.0.0",
    description="AI-powered README generator CLI tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="AI README Generator",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "inquirer>=2.10.0",
        "rich>=13.0.0",
        "google-generativeai>=0.3.0",
        "gitpython>=3.1.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-readme=ai_readme_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)