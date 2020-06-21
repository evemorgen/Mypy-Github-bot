import logging
import os
from dataclasses import dataclass
from typing import List

import toml
import toml.decoder

logger = logging.getLogger(__name__)

REPOS_PREFIX = "."  # local devel
# REPOS_PREFIX = "/app" # heroku

GH_SECRET = os.environ["GH_SECRET"]
GH_APP_ID = os.environ["GH_APP_ID"]
GH_PRIVATE_KEY = os.environ["GH_PRIVATE_KEY"]
GH_REVIEW_USER = 64769253
PORT = int(os.environ.get("PORT", 3000))

MYPY_ADDITIONAL_ARGS = "--ignore-missing-imports"


@dataclass
class RepoOpts:
    starting_points: List[str] = ["."]
    additional_mypy_opts: str = ""


def get_repo_configuration(repo_name: str) -> RepoOpts:
    configuration = {}
    try:
        toml_dict = toml.load(f"{REPOS_PREFIX}/{repo_name}/pyproject.toml")
        configuration = toml_dict["tool"]["mypy-bot"]
    except FileNotFoundError:
        logger.warning(f"No pyproject.toml found in {REPOS_PREFIX}/{repo_name}")
    except toml.decoder.TomlDecodeError:
        logger.warning(f"pyproject.toml in {REPOS_PREFIX}/{repo_name} is invalid.")
    except KeyError:
        logger.warning("No mypy-bot configuration found in pyproject.toml")

    return RepoOpts(**configuration)
