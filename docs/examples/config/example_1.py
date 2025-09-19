import os
from psengine.config import Config, get_config

Config.init(
    config_path=os.path.join(os.getcwd(), "config.toml")
)
config = get_config()
print(config.my_value)
