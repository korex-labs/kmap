from kmap import config
from kmap.command import validate_config


def test_validate_config_reexports_config_validate_config():
    assert validate_config.__all__ == ["validate_config"]
    assert validate_config.validate_config is config.validate_config
