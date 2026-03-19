import os
import json

class SettingsManager:
    """Manages application-wide settings and persistence."""
    
    DEFAULT_SETTINGS = {
        'theme': 'pure_dark',
        'font_scale': 1.0,
        'font_family': 'Inter',
        'high_contrast': False,
        'animations_enabled': True
    }
    
    def __init__(self, user_data_path=None):
        self.user_data_path = user_data_path or os.path.dirname(__file__)
        self.settings_file = os.path.join(self.user_data_path, 'settings_config.json')
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save current settings to JSON file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default if default is not None else self.DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save_settings()

    @property
    def theme(self):
        return self.get('theme')

    @property
    def font_scale(self):
        return self.get('font_scale')
