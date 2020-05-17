import os

from cachetools import TTLCache
from gidgethub import apps, sansio
from git import Repo
from unidiff import PatchSet

from app import config


ttl_cache = TTLCache(10, 600)


async def get_github_token(gh, event):
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
    installation_access_token = await get_github_token(gh, event)
    response = await gh.getitem(
        f"/repos/{repo_name}/pulls/{pr_number}",
        accept=sansio.accept_format(media="diff"),
        oauth_token=installation_access_token["token"],
    )

    return PatchSet(response)


def generate_repo_url(access_token, repo_name):
    return f"https://x-access-token:{access_token}@github.com/{repo_name}.git"


async def clone_repo(repo_name, gh, event) -> Repo:
    gh_token = await get_github_token(gh, event)
    if not os.path.exists(f"{config.REPOS_PREFIX}/{repo_name}"):
        Repo.clone_from(
            url=generate_repo_url(gh_token["token"], repo_name), to_path=f"{config.REPOS_PREFIX}/{repo_name}"
        )

    repo = Repo(f"{config.REPOS_PREFIX}/{repo_name}")
    return repo


async def submit_review(repo_name, pr_number, payload, gh, event):
    body = {
        "body": "Good stuff!",
        "commit_id": payload["commit_sha"],
        "event": "COMMENT",
        "comments": [{"path": payload["file_path"], "position": int(payload["line_number"]), "body": payload["body"],}],
    }
    url = f"/repos/{repo_name}/pulls/{pr_number}/reviews"
    installation_access_token = await get_github_token(gh, event)

    await gh.post(url, data=body, oauth_token=installation_access_token["token"])
