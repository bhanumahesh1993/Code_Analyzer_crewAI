"""
Configuration module for the Code Analyzer.
Handles loading YAML configs and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Default configuration paths
DEFAULT_AGENTS_CONFIG = os.path.join(os.path.dirname(__file__), "agents.yaml")
DEFAULT_TASKS_CONFIG = os.path.join(os.path.dirname(__file__), "tasks.yaml")


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        file_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing the configuration
    
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML file is invalid
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")


def load_agents_config(config_path: str = DEFAULT_AGENTS_CONFIG) -> Dict[str, Any]:
    """
    Load agent configurations from YAML.
    
    Args:
        config_path: Path to the agents configuration file
        
    Returns:
        Dictionary containing agent configurations
    """
    return load_yaml_config(config_path)


def load_tasks_config(config_path: str = DEFAULT_TASKS_CONFIG) -> Dict[str, Any]:
    """
    Load task configurations from YAML.
    
    Args:
        config_path: Path to the tasks configuration file
        
    Returns:
        Dictionary containing task configurations
    """
    return load_yaml_config(config_path)


def get_env_var(name: str, default: Any = None) -> Any:
    """
    Get environment variable with fallback.
    
    Args:
        name: Name of the environment variable
        default: Default value if the environment variable doesn't exist
        
    Returns:
        Value of the environment variable or the default
    """
    return os.environ.get(name, default)


def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment variables.
    
    Returns:
        OpenAI API key
        
    Raises:
        ValueError: If the API key is not set
    """
    api_key = get_env_var("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        )
    return api_key


def get_default_model() -> str:
    """Get the default LLM model from environment or use a fallback."""
    return get_env_var("DEFAULT_MODEL", "gpt-3.5-turbo")


def get_model_temperature() -> float:
    """Get the model temperature from environment or use a fallback."""
    temp = get_env_var("MODEL_TEMPERATURE", "0.2")
    return float(temp)


def get_default_output_dir() -> str:
    """Get the default output directory from environment or use a fallback."""
    return get_env_var("DEFAULT_OUTPUT_DIR", "./output")