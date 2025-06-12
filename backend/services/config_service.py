import json
import os


def _get_config_path():
    return os.path.join(os.path.dirname(__file__), '../config.json')


class Config:
    _config = None

    @classmethod
    def load(cls, path=None):
        if cls._config is None:
            if path is None:
                path = _get_config_path()
            with open(path) as f:
                cls._config = json.load(f)
        return cls._config

    @classmethod
    def reload(cls, path=None):
        if path is None:
            path = _get_config_path()
        with open(path) as f:
            cls._config = json.load(f)
        return cls._config


def get_config():
    """
    Läser och returnerar konfigurationen från config.json.
    :return: dict med konfigurationsdata
    """
    with open(_get_config_path(), "r") as f:
        return json.load(f)


def update_config(data):
    """
    Uppdaterar config.json med ny data.
    :param data: dict med nya konfigurationsvärden
    """
    with open(_get_config_path(), "w") as f:
        json.dump(data, f, indent=4)
