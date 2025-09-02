from psengine.config import Config, get_config

Config.init(my_value=5)
config = get_config()
print(config.my_value)
