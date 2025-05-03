from app.services.github_service import GitHubService


class MockGitHubService(GitHubService):
    def __init__(self):
        # No need for a real token
        self.access_token = "dummy_token"
        self.base_url = "https://api.github.com"
        self.headers = {}

    async def _github_request(self, endpoint, method="GET", params=None, data=None):
        # Return mock data based on the endpoint
        if "/repos/" in endpoint and endpoint.endswith("/contents"):
            return [{"name": "test_file.py", "type": "file", "path": "test_file.py"}]
        elif "/repos/" in endpoint and not endpoint.endswith("/contents"):
            return {
                "name": "test-repo",
                "full_name": "test-user/test-repo",
                "description": "Test repository",
                "language": "Python",
                "topics": ["api", "testing"],
                "default_branch": "main",
            }
        # Add more mock responses as needed
        return {}

    # Override other methods as needed with test data
    async def get_repository_details(self, repo_url):
        return {
            "name": "test-repo",
            "full_name": "test-user/test-repo",
            "description": "Test repository for README generation",
            "language": "Python",
            "languages": {"Python": 10000},
            "topics": ["api", "testing", "documentation"],
            "default_branch": "main",
            "license": "MIT",
            "stars": 42,
            "forks": 10,
            "contributors": [{"name": "test-user", "contributions": 100}],
        }

    async def get_repository_file_structure(
        self, repo_url, path="", max_depth=3, max_files=100
    ):
        return "README.md\ntest_file.py\nsrc/\n  └── main.py\n  └── utils.py"

    async def get_code_samples(self, repo_url):
        return {"test_file.py": "def test_function():\n    return 'Hello, world!'"}
