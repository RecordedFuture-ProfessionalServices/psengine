from pathlib import Path

from psengine.config import get_config

CONFIG_PATH = Path.cwd() / 'config.toml'

config = get_config()
print(config.my_value)
