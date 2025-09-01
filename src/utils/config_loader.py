"""Configuration loader utility"""

import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger


class ConfigLoader:
    """Load and manage YAML configuration files"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._configs = {}

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a specific configuration file

        Args:
            config_name: Name of config file (without .yaml extension)

        Returns:
            Dictionary containing configuration
        """
        if config_name in self._configs:
            return self._configs[config_name]

        config_path = self.config_dir / f"{config_name}.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self._configs[config_name] = config
            logger.info(f"Loaded configuration: {config_name}")
            return config

        except yaml.YAMLError as e:
            logger.error(f"Error loading config {config_name}: {e}")
            raise

    def load_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load all configuration files

        Returns:
            Dictionary with config names as keys
        """
        config_files = ["data_config", "labeling_config", "model_config"]

        for config_name in config_files:
            try:
                self.load_config(config_name)
            except FileNotFoundError:
                logger.warning(f"Config file not found: {config_name}.yaml")
                continue

        return self._configs

    def get_config(self, config_name: str) -> Dict[str, Any]:
        """Get loaded configuration

        Args:
            config_name: Name of configuration

        Returns:
            Configuration dictionary
        """
        if config_name not in self._configs:
            return self.load_config(config_name)
        return self._configs[config_name]

    def update_config(self, config_name: str, updates: Dict[str, Any]) -> None:
        """Update configuration in memory

        Args:
            config_name: Name of configuration
            updates: Dictionary of updates to apply
        """
        if config_name not in self._configs:
            self.load_config(config_name)

        self._configs[config_name].update(updates)
        logger.info(f"Updated configuration: {config_name}")


# Global config loader instance
config_loader = ConfigLoader()
