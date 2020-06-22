import dataclasses
import logging
import os
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


@dataclasses.dataclass
class RepoOpts:
    starting_points: List[str] = dataclasses.field(default_factory=lambda: ["."])
    additional_mypy_opts: str = ""


def get_repo_configuration(repo_name: str) -> RepoOpts:
    try:
        logger.info(f"{REPOS_PREFIX}/{repo_name}/pyproject.toml")
        toml_dict = toml.load(f"{REPOS_PREFIX}/{repo_name}/pyproject.toml")
        configuration = toml_dict["tool"]["mypy-bot"]
        return RepoOpts(**configuration)
    except FileNotFoundError:
        logger.warning(f"No pyproject.toml found in {REPOS_PREFIX}/{repo_name}")
    except toml.decoder.TomlDecodeError:
        logger.warning(f"pyproject.toml in {REPOS_PREFIX}/{repo_name} is invalid.")
    except KeyError:
        logger.warning("No mypy-bot configuration found in pyproject.toml")
    except TypeError:
        logger.warning("Illegal parameter value in pyproject toml")

    return RepoOpts()
