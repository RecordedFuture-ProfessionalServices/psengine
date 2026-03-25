import json
import os

import pytest
from pydantic import ValidationError

from psengine.config import Config, ConfigFileError, get_config


class Test_Config:
    def test_config_from_env_defined_values(self, monkeypatch):
        Config.reset_instance()
        monkeypatch.setenv('RF_CLIENT_RETRIES', '2')
        monkeypatch.setenv('RF_CLIENT_POOL_MAX_SIZE', '4')
        Config.init()
        gc = get_config()
        assert gc.client_retries == 2
        assert gc.client_pool_max_size == 4

    def test_config_from_env_dont_read_undefined_values(self, monkeypatch):
        Config.reset_instance()
        monkeypatch.setenv('RF_MOISE', 'moise')
        Config.init()
        gc = get_config()

        with pytest.raises(AttributeError):
            assert gc.moise is None

    def test_config_from_toml(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / 'config.toml'
        toml_data = """client_retries = 2
        moise = 'moise'
        """
        path.write_text(toml_data)
        Config.init(config_path=path)
        gc = get_config()

        assert gc.moise == 'moise'
        assert gc.client_retries == 2

    def test_config_empty_toml(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / 'config.toml'
        toml_data = """client_retries = 2
        moise = 'moise'
        """
        path.write_text(toml_data)
        Config.init(config_path=path)
        gc = get_config()

        path = tmp_path / 'config2.toml'
        path.write_text('')
        Config.init(config_path=path)
        gc = get_config()

        assert gc.app_id is None

    def test_config_from_json(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / 'config.json'
        json_data = {
            'rf_token': 'a' * 32,
            'moise': 'moise',
            'client_retries': 5,
        }
        path.write_text(json.dumps(json_data))
        Config.init(config_path=path)
        gc = get_config()
        assert gc.moise == 'moise'
        assert gc.rf_token.get_secret_value() == 'a' * 32
        assert gc.client_retries == 5

    def test_config_from_dotenv(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / '.env'
        dotenv_data = """client_retries = 2
        moise = 'moise'
        """
        path.write_text(dotenv_data)
        Config.init(config_path=path)
        gc = get_config()
        assert gc.moise == 'moise'
        assert gc.client_retries == 2

    def test_config_from_init(self):
        Config.reset_instance()
        Config.init(moise='moise', test='test', client_retries=2)
        gc = get_config()
        assert gc.moise == 'moise'
        assert gc.client_retries == 2
        assert gc.test == 'test'

    def test_precedence_init_vs_toml(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / 'config.toml'
        toml_data = """client_retries = 2
        moise = 'moise'
        something = 'something'
        """
        path.write_text(toml_data)
        Config.init(config_path=path, moise='moisemoise', client_retries=9)
        gc = get_config()

        assert gc.moise == 'moisemoise'
        assert gc.client_retries == 9
        assert gc.something == 'something'

    def test_precedence_env_vs_toml(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / 'config.toml'
        toml_data = """client_retries = 2
        moise = 'moise'
        """
        os.environ['RF_HTTP_PROXY'] = 'moise2'
        os.environ['RF_CLIENT_POOL_MAX_SIZE'] = '4'

        path.write_text(toml_data)

        Config.init(config_path=path)
        gc = get_config()

        assert gc.moise == 'moise'
        assert gc.client_retries == 2
        assert gc.client_pool_max_size == 4

    def test_prcedence_of_init_vs_env(self, monkeypatch):
        Config.reset_instance()
        monkeypatch.setenv('RF_CLIENT_RETRIES', '2')
        monkeypatch.setenv('RF_CLIENT_POOL_MAX_SIZE', '4')
        os.environ['RF_CLIENT_RETRIES'] = 'moise'

        Config.init(moise='moisemoise', client_retries=20)
        gc = get_config()

        assert gc.moise == 'moisemoise'
        assert gc.client_retries == 20
        assert gc.client_pool_max_size == 4

    def test_valid_token(self):
        Config.reset_instance()
        Config.init(rf_token='a' * 32, asi_token='b' * 32)
        gc = get_config()
        assert gc.rf_token.get_secret_value() == 'a' * 32
        assert gc.asi_token.get_secret_value() == 'b' * 32

    def test_invalid_token_raises_ValidationError(self):
        Config.reset_instance()
        with pytest.raises(ValidationError):
            Config.init(rf_token='moise')  # noqa: S106

    def test_save_config(self, tmp_path):
        Config.reset_instance()
        config_dir = tmp_path / 'config'
        config_path = config_dir / 'config.json'
        Config.init(rf_token='a' * 32, moise='moise', client_retries=9)

        gc = get_config()
        gc.save_config(config_dir, 'config.json')

        assert config_path.exists()
        assert 'moise' in config_path.read_text()
        assert 'token' not in config_path.read_text()
        assert 'client_retries' in config_path.read_text()

    def test_config_raises_ValueError_wrong_extension(self, tmp_path):
        Config.reset_instance()
        path = tmp_path / 'config.moise'
        path.touch()
        with pytest.raises(
            ValueError, match='The config file extension must be .toml or .json or .env'
        ):
            Config.init(config_path=path)

    def test_reset_config(self):
        Config.init(moise='moise')
        gc = get_config()
        assert gc.moise == 'moise'
        Config.reset_instance()
        Config.init()
        gc = get_config()
        with pytest.raises(AttributeError):
            assert gc.moise

    def test_config_init_raise_ConfigError_missing_file(self, tmp_path):
        with pytest.raises(ConfigFileError):
            Config.init(config_path=tmp_path / 'something.toml')

    def test_config_cannot_be_changed(self):
        Config.init()
        gc = get_config()

        with pytest.raises(ValidationError):
            gc.rf_token = 'a' * 32
