# -*- coding: utf-8 -*-
"""Top level package for {{cookiecutter.package_name}}."""

from {{cookiecutter.package_name}}.logger import configure_logging
from {{cookiecutter.package_name}}.settings import Settings


SETTINGS = Settings()

logger = configure_logging(
   "{{cookiecutter.package_name}}", SETTINGS, kidnap_loggers=True
)
