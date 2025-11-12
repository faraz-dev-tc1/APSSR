"""
Configuration loader utility
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Loads and manages system configuration"""

    def __init__(self, config_path: str = None):
        """Initialize configuration loader"""
        # Load environment variables
        load_dotenv()

        # Determine config path
        if config_path is None:
            base_path = Path(__file__).parent.parent.parent
            config_path = base_path / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._load_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_env_overrides(self):
        """Override config with environment variables"""
        # Google API Key
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            self.config['gemini']['api_key'] = api_key

        # Model override
        model = os.getenv('GEMINI_MODEL')
        if model:
            self.config['gemini']['model'] = model

        # Processing settings
        max_workers = os.getenv('MAX_WORKERS')
        if max_workers:
            self.config['system']['max_workers'] = int(max_workers)

        enable_validation = os.getenv('ENABLE_VALIDATION')
        if enable_validation:
            self.config['system']['enable_validation'] = enable_validation.lower() == 'true'

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('gemini.model')
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_gemini_config(self) -> Dict[str, Any]:
        """Get Gemini-specific configuration"""
        return self.config.get('gemini', {})

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get module-specific configuration"""
        return self.config.get(module_name, {})


# Global configuration instance
_config_instance = None


def get_config() -> ConfigLoader:
    """Get or create global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
