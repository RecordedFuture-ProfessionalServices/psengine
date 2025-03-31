#################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import logging
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Optional, Union

from pydantic import Field, Secret, field_validator, validate_call
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from ..constants import (
    BACKOFF_FACTOR,
    POOL_MAX_SIZE,
    REQUEST_TIMEOUT,
    RETRY_TOTAL,
    RF_TOKEN_ENV_VAR,
    RF_TOKEN_VALIDATION_REGEX,
    ROOT_DIR,
    SSL_VERIFY,
    STATUS_FORCELIST,
)
from ..helpers import OSHelpers
from .errors import ConfigFileError

PLAT_REGEX = r'^([A-Z]|[a-z])+(\/\d+)?((\.\d+)*?)$'
APP_ID_REGEX = r'^\S+\/\d+((\.\d+)*?)$'


class RFToken(Secret[str]):
    """Recorded Future token mask."""

    def _display(self) -> str:
        return '********' + self.get_secret_value()[-4:]


class ConfigModel(BaseSettings):
    """Global configuration settings.

    This class is used to store global configuration settings for the application.

    Supports config with .toml, .json and .env extensions.
    Regular expression validation:

        - app_id must be ``<str>/<int>[.<int>][.<int>]``
        - platform_id must be ``<str>[/<int>][.<int>][.<int>]``

    Example:
        Initialize the ``Config`` with ``config_path``

        .. code-block:: python
            :linenos:

            from psengine.config import Config, get_config
            Config.init(config_path=<filepath>)

            config = get_config()

        Initialize the ``Config`` from python itself:

        .. code-block:: python
            :linenos:

            from psengine.config import Config, get_config
            Config.init(my_setting='example', my_second_setting='example2')

            config = get_config()
            config.my_setting
    """

    config_path: Union[str, Path, None] = None
    model_config = SettingsConfigDict(arbitrary_types_allowed=True, extra='allow', frozen=True)

    platform_id: Optional[str] = Field(default=None, pattern=PLAT_REGEX, examples=['Splunk/8.0.0'])
    app_id: Optional[str] = Field(default=None, pattern=APP_ID_REGEX, examples=['get-alerts/1.0.0'])
    rf_token: Optional[RFToken] = Field(default=os.environ.get(RF_TOKEN_ENV_VAR, ''))
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    client_ssl_verify: Optional[bool] = SSL_VERIFY
    client_basic_auth: Optional[tuple[str, str]] = None
    client_cert: Optional[Union[str, tuple[str, str]]] = None
    client_timeout: Optional[int] = REQUEST_TIMEOUT
    client_retries: Optional[int] = RETRY_TOTAL
    client_backoff_factor: Optional[int] = BACKOFF_FACTOR
    client_status_forcelist: Optional[list[int]] = STATUS_FORCELIST
    client_pool_max_size: Optional[int] = POOL_MAX_SIZE

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Set config file sources correctly for Config.

        In the case where a value is specified for the same Settings field in multiple ways, the
        selected value is determined as follows (in descending order of priority):

            1. Arguments passed to the Config class initialiser (``Config.init``)
            2. Environment variables
            3. Config file specified in the config_path field
            4. Variables loaded from the secrets directory
            5. Default values for the Config model

        Args:
            settings_cls (Type[BaseSettings]): class settings
            init_settings (PydanticBaseSettingsSource): initial settings callable
            env_settings (PydanticBaseSettingsSource): environment settings callable
            dotenv_settings (PydanticBaseSettingsSource): .env file settings callable
            file_secret_settings (PydanticBaseSettingsSource): secrets file settings callable

        Returns:
            Tuple[PydanticBaseSettingsSource, ...]: A tuple containing the sources and their order
                                                    for loading the settings values.
        """
        env_settings = EnvSettingsSource(settings_cls, env_prefix='RF_', env_nested_delimiter='__')
        sources = [
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        ]

        if config := init_settings.init_kwargs.get('config_path'):
            config = config if isinstance(config, str) else config.as_posix()
            if config.endswith('.toml'):
                sources.insert(2, TomlConfigSettingsSource(settings_cls, Path(config)))
            elif config.endswith('.json'):
                sources.insert(2, JsonConfigSettingsSource(settings_cls, Path(config)))
            elif config.endswith('.env'):
                sources.insert(
                    2,
                    DotEnvSettingsSource(
                        settings_cls,
                        env_file=Path(config),
                        env_nested_delimiter='.',
                        env_prefix='RF_',
                    ),
                )
            else:
                raise ValueError('The config file extension must be .toml or .json or .env')
        return tuple(sources)

    @field_validator('rf_token', mode='before')
    @classmethod
    def validate_token(cls, rf_token):
        """Validate Recorded Future token.

        Args:
            rf_token (str): Recorded Future token

        Raises:
            ValueError: when token is not 32 alphanumeric characters in ``[a-f][0-9]`` range.

        Returns:
            str: token
        """
        rf_token = rf_token or os.environ.get(RF_TOKEN_ENV_VAR)
        if not rf_token:
            # Edge case: when RF_RF_TOKEN env var is set, it is used and RF_TOKEN is ignored
            # So we check if RF_TOKEN is set and validate it
            return ''
        if not re.match(RF_TOKEN_VALIDATION_REGEX, rf_token):
            raise ValueError(
                f'Invalid Recorded Future API token, must match regex {RF_TOKEN_VALIDATION_REGEX}'
            )

        return rf_token

    @validate_call
    def save_config(
        self,
        directory: Union[str, Path] = Path(ROOT_DIR) / 'config',
        file: Union[str, Path] = 'config.json',
    ):
        """Writes the current values in Config, in the file provided as JSON.

        If the file already exists, the content will be deleted.
        The config will be saved in the ``<project_directory>/config/config.json``

        """
        directory = Path(directory)
        log = logging.getLogger(__name__)
        data = self.model_dump_json(exclude='rf_token', indent=4)
        OSHelpers.mkdir(directory)
        config_path = directory / file
        log.info(f'Saving config in {config_path.as_posix()}')

        with config_path.open('w') as f:
            f.write(data)


class Config:
    """Singleton class to manage Config instances.

    Note that the config is Read Only. Once initialized, attributes cannot be changed unless you
    initialize the config with new values.
    """

    _instance = None

    @classmethod
    def _get_instance(cls) -> Union[ConfigModel, None]:
        """Get instance of ``Config``.

        ``get_config()`` should be used instead of calling this method directly
        """
        if not cls._instance:
            cls._instance = ConfigModel()

        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Method used for testing to clear up the previous instances of ``Config``."""
        cls._instance = None

    @classmethod
    def init(cls, config_class=ConfigModel, **kwargs):
        """Initialize Config instance.

        Call directly on class ``Config.init(config_path=<filepath>)``

        Args:
            config_class (ConfigModel): ConfigModel class
            config_path (str): Path to the config file
            platform_id (str): Name & version of the tool this integrates with, example: ES/8.0.0
            app_id (str): Name & version of the integration itself, example: get-alerts/1.0.0
            rf_token (str): Recorded Future API token
            http_proxy (str): HTTP proxy
            https_proxy (str): HTTPS proxy
            client_ssl_verify (bool): SSL verification. Default is True
            client_basic_auth (tuple): Basic auth credentials
            client_cert (str or tuple): Client certificate
            client_timeout (int): Request timeout. Default is 120
            client_retries (int): Request retries. Default is 5
            client_backoff_factor (int): Request backoff factor. Default is 1
            client_status_forcelist (list): Request status forcelist. Default is [502, 503, 504]
            client_pool_max_size (int): Request pool max size. Default is 120
            kwargs: Additional arguments

        """
        config_path = kwargs.get('config_path')
        if config_path and not Path(config_path).exists():
            raise ConfigFileError(f'File {config_path} does not exists.')

        log = logging.getLogger(__name__)
        cls._instance = config_class(**kwargs)
        gc = cls._instance

        config = deepcopy(gc.model_dump())
        config.update(gc.model_extra)
        log.info(f'Configuration Settings: {config}')


def get_config():
    """Return an instance of ``Config``.

    Use this instead of initializing Config directly, so that the same instance is used.
    """
    return Config._get_instance()
