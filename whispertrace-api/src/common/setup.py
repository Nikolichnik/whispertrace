"""
Setup module.
"""

import logging.config as config

import yaml

from dynaconf import Dynaconf

from common.constants import ENCODING_UTF8


def get_config_settings():
    """
    Get the configuration settings.
    """
    return Dynaconf(envvar_prefix=False, settings_files=["settings.toml"])


def set_up_logging(configuration_path: str) -> None:
    """
    Set up logging based on the logging configuration.

    Args:
        configuration_path (str): The path to the logging configuration file.

    Returns:
        None
    """
    with open(configuration_path, "r", encoding=ENCODING_UTF8) as fh:
        logging_config = yaml.safe_load(fh.read())

        config.dictConfig(logging_config)
