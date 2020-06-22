import logging
import os
import random
import shutil
from typing import Dict, List

from app import config
from cachetools import TTLCache
from gidgethub import apps, sansio
from git import Repo, exc
from unidiff import PatchSet

PRAISES = ["Good job!", "Good stuff!", "Nicely done." "Awesome."]

WTFS = ["(╯°□°)╯︵ ┻━┻", "\\(!!˚☐˚)/", "ಥ_ಥ", "＼(｀0´)／"]

logger = logging.getLogger(__name__)
ttl_cache = TTLCache(10, 600)


async def get_github_token(gh, event) -> Dict[str, str]:
    installation_id = event.data["installation"]["id"]
    if "installation_access_token" in ttl_cache:
        return ttl_cache["installation_access_token"]
    else:
        installation_access_token = await apps.get_installation_access_token(
            gh, installation_id=installation_id, app_id=config.GH_APP_ID, private_key=config.GH_PRIVATE_KEY
        )
        ttl_cache["installation_access_token"] = installation_access_token
        return installation_access_token


async def get_pr_diff(repo_name: str, pr_number: int, gh, event) -> str:
    logger.info(f"Fetching diff in PR:{pr_number} in repo:{repo_name}")
    installation_access_token = await get_github_token(gh, event)
    response = await gh.getitem(
        f"/repos/{repo_name}/pulls/{pr_number}",
        accept=sansio.accept_format(media="diff"),
        oauth_token=installation_access_token["token"],
    )

    return PatchSet(response)


async def get_pr_reviews(repo_name: str, pr_number: int, gh, event) -> List[str]:
    logger.info(f"Fetching reviwes in PR:{pr_number} in repo:{repo_name}")
    installation_access_token = await get_github_token(gh, event)
    response = await gh.getitem(
        f"/repos/{repo_name}/pulls/{pr_number}/reviews", oauth_token=installation_access_token["token"],
    )
    return [review for review in response if review["user"]["id"] == config.GH_REVIEW_USER]


async def get_pr_comments(repo_name: str, pr_number: int, gh, event):
    logger.info(f"Fetching PR comments in PR:{pr_number} in repo:{repo_name}")
    installation_access_token = await get_github_token(gh, event)
    response = await gh.getitem(
        f"/repos/{repo_name}/pulls/{pr_number}/comments", oauth_token=installation_access_token["token"],
    )
    return response


async def update_pr_comment(repo_name: str, pr_number: int, comment_id: int, body: str, gh, event) -> bool:
    installation_access_token = await get_github_token(gh, event)
    await gh.patch(
        f"/repos/{repo_name}/pulls/comments/{comment_id}",
        data={"body": body},
        oauth_token=installation_access_token["token"],
    )
    return True


async def resolve_gh_comment(repo_name: str, pr_number: int, comment_id: int, body: str, gh, event):
    logger.info(f"Resolving comment:{comment_id} in PR:{pr_number} in repo:{repo_name}")
    return await update_pr_comment(repo_name, pr_number, comment_id, body, gh, event)


def generate_repo_url(access_token, repo_name):
    return f"https://x-access-token:{access_token}@github.com/{repo_name}.git"


async def clone_repo(repo_name, gh, event) -> Repo:
    gh_token = await get_github_token(gh, event)
    if not os.path.exists(f"{config.REPOS_PREFIX}/{repo_name}"):
        logger.info(f"Repo not found, cloning repo:{repo_name}")
        Repo.clone_from(
            url=generate_repo_url(gh_token["token"], repo_name),
            to_path=f"{config.REPOS_PREFIX}/{repo_name}",
            # single_branch=True,
        )

    repo = Repo(f"{config.REPOS_PREFIX}/{repo_name}")

    _git = repo.git

    try:
        logger.info(f"fetching all branches in {repo_name}")
        _git.fetch(all=True)
    except exc.GitCommandError:
        logger.info(f"Fetching content failed, probably token has expired. Removing repo:{repo_name} and rerunning.")
        shutil.rmtree(f"{config.REPOS_PREFIX}/{repo_name}")
        return await clone_repo(repo_name, gh, event)
    return repo


async def submit_review(repo_name, pr_number, payload, gh, event):
    logger.info(f"Submitting review in PR:{pr_number}, repo:{repo_name}")
    comment_body = f"I found {len(payload['body'])} mypy errors. " + (
        random.choice(PRAISES) if len(payload["body"]) < 5 else random.choice(WTFS)
    )

    body = {
        "body": comment_body,
        "commit_id": payload["commit_sha"],
        "event": "COMMENT",
        "comments": [{"path": err.file, "position": err.diff_position, "body": str(err)} for err in payload["body"]],
    }
    url = f"/repos/{repo_name}/pulls/{pr_number}/reviews"
    installation_access_token = await get_github_token(gh, event)

    await gh.post(url, data=body, oauth_token=installation_access_token["token"])
