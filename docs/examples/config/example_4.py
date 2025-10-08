from pathlib import Path

from psengine.config import Config, ConfigModel, get_config
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).parent / 'custom_config.toml'


class ComplexValue(BaseModel):
    """Model to define the `complex_value` table."""

    data: list[str]
    value: list[int]


class IntegrationConfig(ConfigModel):
    """The class of my integration config."""

    simple_value: int
    complex_value: ComplexValue


Config.init(
    config_class=IntegrationConfig, config_path=CONFIG_PATH
)
config = get_config()

print(config)
print(config.simple_value)
print(config.complex_value.data)
print(config.complex_value.value)
