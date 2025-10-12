# -*- coding: utf-8 -*-
"""
Configuration Manager
Handles persistent storage of application settings in JSON format
"""

import os
import json


class ConfigManager:
    """Manage application configuration stored in JSON file"""

    def __init__(self, config_file_path):
        """Initialize config manager

        Args:
            config_file_path: Absolute path to config.json file
        """
        self.config_file = config_file_path
        self.config = self._load_config()

    def _load_config(self):
        """Load config from file, create with defaults if doesn't exist"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Ensure required keys exist
                    if 'search_roots' not in config:
                        config['search_roots'] = []
                    return config
            except (IOError, ValueError) as e:
                # Config file corrupted or unreadable - use defaults
                return self._get_defaults()
        else:
            # Config file doesn't exist - create with defaults
            config = self._get_defaults()
            self._save_config(config)
            return config

    def _get_defaults(self):
        """Get default configuration"""
        return {
            'search_roots': []
        }

    def _save_config(self, config):
        """Save config to file

        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            raise Exception("Failed to save config: %s" % str(e))

    def get_search_roots(self):
        """Get list of search root directories

        Returns:
            list: List of directory paths
        """
        return self.config.get('search_roots', [])

    def set_search_roots(self, roots):
        """Set list of search root directories

        Args:
            roots: List of directory paths
        """
        self.config['search_roots'] = list(roots)
        self._save_config(self.config)

    def add_search_root(self, path):
        """Add a search root directory

        Args:
            path: Directory path to add
        """
        if 'search_roots' not in self.config:
            self.config['search_roots'] = []

        if path not in self.config['search_roots']:
            self.config['search_roots'].append(path)
            self._save_config(self.config)

    def remove_search_root(self, path):
        """Remove a search root directory

        Args:
            path: Directory path to remove
        """
        if 'search_roots' in self.config and path in self.config['search_roots']:
            self.config['search_roots'].remove(path)
            self._save_config(self.config)
