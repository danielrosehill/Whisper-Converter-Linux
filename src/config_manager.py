import os
import json
from pathlib import Path

class ConfigManager:
    """Manages configuration settings for the application, including API keys."""
    
    def __init__(self):
        """Initialize the config manager with default paths."""
        self.config_dir = Path.home() / ".config" / "whisper-converter"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self.config = self._load_config()
    
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """Load configuration from file or create default if it doesn't exist."""
        if not self.config_file.exists():
            default_config = {
                "openai_api_key": "",
                "whisper_model": "whisper-1",
                "text_model": "gpt-4o-mini"
            }
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or doesn't exist, return default config
            return {
                "openai_api_key": "",
                "whisper_model": "whisper-1",
                "text_model": "gpt-4o-mini"
            }
    
    def save_config(self):
        """Save the current configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)
    
    def get_openai_api_key(self):
        """Get the OpenAI API key."""
        return self.config.get("openai_api_key", "")
    
    def set_openai_api_key(self, api_key):
        """Set the OpenAI API key and save the configuration."""
        self.config["openai_api_key"] = api_key
        self.save_config()
    
    def get_whisper_model(self):
        """Get the preferred Whisper model."""
        return self.config.get("whisper_model", "whisper-1")
    
    def set_whisper_model(self, model):
        """Set the preferred Whisper model and save the configuration."""
        self.config["whisper_model"] = model
        self.save_config()
    
    def get_text_model(self):
        """Get the preferred text model for cleaning and title generation."""
        return self.config.get("text_model", "gpt-4o-mini")
    
    def set_text_model(self, model):
        """Set the preferred text model and save the configuration."""
        self.config["text_model"] = model
        self.save_config()
