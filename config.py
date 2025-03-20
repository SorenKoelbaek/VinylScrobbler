"""Configuration settings for the application."""

import os

from dynaconf import Dynaconf
from dependencies.log_setup import get_logger, SingleLineFormatter

logger = get_logger(__name__)
current_directory = os.path.dirname(os.path.realpath(__file__))

settings = Dynaconf(
	root_path=current_directory,
	envvar_prefix="DYNACONF",
	settings_files=["settings.toml","secrets.toml"],
	load_dotenv=True,
	environments=True,
)

