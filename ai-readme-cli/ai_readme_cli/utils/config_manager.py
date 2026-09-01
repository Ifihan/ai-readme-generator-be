import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class ConfigManager:
    def __init__(self):
        self.config_path = Path.home() / '.ai-readme-config.json'

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Invalid config file, return defaults
                return {}
        return {}

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from environment or config."""
        # Check environment variable first
        env_key = os.getenv('GEMINI_API_KEY')
        if env_key:
            return env_key

        # Check config file
        config = self.load_config()
        return config.get('gemini_api_key')

    def set_gemini_api_key(self, api_key: str) -> None:
        """Set Gemini API key in config."""
        config = self.load_config()
        config['gemini_api_key'] = api_key
        self.save_config(config)

    def get_default_sections(self) -> List[str]:
        """Get default sections from config."""
        config = self.load_config()
        return config.get('default_sections', [
            'introduction', 'features', 'installation', 'usage', 'contributing', 'license'
        ])

    def set_default_sections(self, sections: List[str]) -> None:
        """Set default sections in config."""
        config = self.load_config()
        config['default_sections'] = sections
        self.save_config(config)

    def get_output_file_name(self) -> str:
        """Get output file name from config."""
        config = self.load_config()
        return config.get('output_file_name', 'README.md')

    def set_output_file_name(self, file_name: str) -> None:
        """Set output file name in config."""
        config = self.load_config()
        config['output_file_name'] = file_name
        self.save_config(config)