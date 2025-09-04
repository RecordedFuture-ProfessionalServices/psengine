from pathlib import Path
from psengine.config import Config, get_config

Config.init(
    config_path=Path(__file__).parent / "config.toml"
)
config = get_config()
print(config.my_value)
