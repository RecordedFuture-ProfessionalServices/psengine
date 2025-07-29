from pydantic import BaseModel

from psengine.classic_alerts import ClassicAlertMgr
from psengine.config import Config, ConfigModel, get_config
from psengine.enrich import LookupMgr


def test_managers_without_config():
    """This test is made to verify that Managers can be init without a config."""
    LookupMgr()
    ClassicAlertMgr()


def test_custom_int_config():
    """Test for custom integration config."""

    class Data(BaseModel):
        x: int
        y: str

    class AnomaliConfig(ConfigModel):
        data: Data

    Config.init(config_class=AnomaliConfig, data={'x': 3, 'y': 'moise'})
    gc = get_config()

    assert isinstance(gc, AnomaliConfig)
    assert gc.data.x == 3
    assert gc.data.y == 'moise'
