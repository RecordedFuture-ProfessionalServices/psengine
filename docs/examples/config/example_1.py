from pathlib import Path

from psengine.config import Config, get_config

CONFIG_PATH = Path(__file__).parent / 'config.toml'

Config.init(config_path=CONFIG_PATH)
config = get_config()
print(config.my_value)
