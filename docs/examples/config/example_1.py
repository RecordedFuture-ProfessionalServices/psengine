from pathlib import Path

from psengine.config import get_config, Config

CONFIG_PATH = Path(__file__).parent / 'config.toml'

Config.init(config_path=CONFIG_PATH)
config = get_config()
print(config.my_value)
