import json
import logging

logger = logging.getLogger(__name__)

def load_config(filepath):
    """
    Loads a JSON configuration from the given file path.
    Raises an exception if there is an error.
    """
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error("Error loading config from %s: %s", filepath, e)
        raise

def save_config(config, filepath="transformation_config.json"):
    """
    Saves the given configuration dictionary as JSON to the specified filepath.
    Raises an exception if there is an error.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("Configuration saved successfully to %s", filepath)
    except Exception as e:
        logger.error("Error saving config to %s: %s", filepath, e)
        raise
