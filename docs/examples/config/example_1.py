from psengine.config import Config, get_config

Config.init(config_path="config.toml")
config = get_config()
print(config.my_value)
