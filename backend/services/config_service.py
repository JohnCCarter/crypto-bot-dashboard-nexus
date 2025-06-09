import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def get_config():
    """
    Läser och returnerar konfigurationen från config.json.
    :return: dict med konfigurationsdata
    """
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def update_config(data):
    """
    Uppdaterar config.json med ny data.
    :param data: dict med nya konfigurationsvärden
    """
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)
