from psengine.config import Config, get_config

Config.init()
config = get_config()
print(config.app_id)
print(config.platform_id)
