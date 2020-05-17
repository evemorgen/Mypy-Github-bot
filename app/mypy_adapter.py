import subprocess
from typing import Set

from app.git_operations import config, clone_repo, get_pr_diff, submit_review


def perform_mypy_check(repo_prefix: str, repo_name: str) -> Set[str]:
    result = subprocess.run(["mypy", f"{repo_prefix}/{repo_name}/."], capture_output=True)
    return set(result.stdout.decode().split("\n"))


async def perform_mypy_thing(event, gh):
    pr_root = event.data["pull_request"]
    branch_from, branch_to = pr_root["head"]["ref"], pr_root["base"]["ref"]
    repo_name = event.data["repository"]["full_name"]

    repo = await clone_repo(repo_name, gh, event)
    git = repo.git

    git.fetch(all=True)
    git.checkout(branch_to)
    first = perform_mypy_check(config.REPOS_PREFIX, repo_name)

    git.checkout(branch_from)
    second = perform_mypy_check(config.REPOS_PREFIX, repo_name)
    print(f"diff: {second - first}")

    for mypy_error in second - first:
        if mypy_error.startswith("Found"):
            continue
        try:
            path, line_no, _, error = mypy_error.split(":", maxsplit=3)
            latest_commit_sha = pr_root["head"]["sha"]
            path = path.replace(repo_name, "")

            payload = {"file_path": path[1:], "line_number": line_no, "commit_sha": latest_commit_sha, "body": error}

            await get_pr_diff(repo_name, pr_root["number"], gh, event)
            await submit_review(repo_name, pr_root["number"], payload, gh, event)
        except Exception as exc:
            raise exc
