from __future__ import annotations

import itertools
import logging
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List, Optional, Set

from app.config import get_repo_configuration
from app.git_operations import (
    clone_repo,
    config,
    get_pr_comments,
    get_pr_diff,
    get_pr_reviews,
    resolve_gh_comment,
    submit_review,
)

if TYPE_CHECKING:
    from unidiff import Hunk, PatchSet


logger = logging.getLogger(__name__)


@dataclass
class MypyError:
    file: str
    line_no: int
    severity: str
    error_body: str

    def calculate_diff_position(self, diff):
        self.diff_position = int(self.line_no) - diff.target_start + 1

    def __str__(self):
        return f"{self.file}:{self.line_no}:{self.severity}:{self.error_body}"

    def __eq__(self, other):
        return self.file == other.file and self.error_body == other.error_body


def perform_mypy_check(repo_name: str) -> Set[str]:
    logger.info(f"Running mypy against {repo_name}")
    repo_opts = get_repo_configuration(repo_name)
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"cd ./{config.REPOS_PREFIX}/{repo_name} && "
            + " ".join(
                ["mypy"]
                + ([repo_opts.additional_mypy_opts] if repo_opts.additional_mypy_opts else [])
                + [f"{file}" for file in repo_opts.starting_points]
            ),
        ],
        capture_output=True,
    )
    logger.debug(f"found errors: {result}")
    return set(elem for elem in result.stdout.decode().split("\n") if elem)


def parse_mypy_output(mypy_errors: Iterable[str], repo_name: Optional[str] = None) -> List[MypyError]:
    parsed_errors = []
    for error in mypy_errors:
        if error.startswith("Found") or error == "" or error.startswith("~~"):
            continue
        file, line_no, severity, error_body = error.split(":", maxsplit=3)
        filename = file.replace(repo_name, "") if repo_name else file
        parsed_errors.append(MypyError(filename.strip(), int(line_no), severity.strip(), error_body.strip()))
    return parsed_errors


def if_error_in_hunk(error: MypyError, hunk: Hunk) -> bool:
    return hunk.target_start + hunk.target_length > int(error.line_no) > hunk.target_start


def filter_errors_in_diff(repo_name: str, mypy_errors: Iterable[str], github_diff: PatchSet) -> Iterable[MypyError]:
    parsed_errors = parse_mypy_output(mypy_errors=mypy_errors, repo_name=repo_name)
    logger.info(parsed_errors)
    filtered_errors = []
    for hunk, error in itertools.product(github_diff, parsed_errors):
        for change in hunk:
            if hunk.path == error.file and if_error_in_hunk(error, change):
                error.calculate_diff_position(change)
                filtered_errors.append(error)
    return filtered_errors


async def perform_mypy_thing(event, gh):
    pr_root = event.data["pull_request"]
    branch_from, branch_to = pr_root["head"]["ref"], pr_root["base"]["ref"]
    repo_name = event.data["repository"]["full_name"]
    latest_commit_sha = pr_root["head"]["sha"]

    repo = await clone_repo(repo_name, gh, event)

    git = repo.git
    git.fetch(all=True)
    git.checkout(branch_to)
    git.pull("origin", branch_to)
    logger.info(f"Pulling {branch_to} in {repo_name}.")

    git.checkout(branch_from)
    git.pull("origin", branch_from)
    logger.info(f"Pulling {branch_from} in {repo_name}.")

    second = perform_mypy_check(repo_name)

    diff = await get_pr_diff(repo_name, pr_root["number"], gh, event)

    mypy_errors = filter_errors_in_diff(repo_name, second, diff)
    logger.info(mypy_errors)
    reviews = await get_pr_reviews(repo_name, pr_root["number"], gh, event)
    if len(reviews) > 0:
        comments = await get_pr_comments(repo_name, pr_root["number"], gh, event)
        posted_mypy_errors = list(
            zip(
                [comment["id"] for comment in comments if not comment["body"].startswith("~~")],
                parse_mypy_output(mypy_errors=[comment["body"] for comment in comments]),
            )
        )
        for comment_id, old_error in posted_mypy_errors:
            if old_error not in mypy_errors:
                await resolve_gh_comment(
                    repo_name, pr_root["number"], comment_id, body=f"~~{str(old_error)}~~", gh=gh, event=event
                )
        if not all((error in [e for _, e in posted_mypy_errors]) for error in mypy_errors):
            new_errors = [error for error in mypy_errors if error not in [e for _, e in posted_mypy_errors]]
            payload = {"commit_sha": latest_commit_sha, "body": new_errors}
            await submit_review(repo_name, pr_root["number"], payload, gh, event)
    else:
        # PR not yet reviewed by mypy-bot
        payload = {"commit_sha": latest_commit_sha, "body": mypy_errors}
        await submit_review(repo_name, pr_root["number"], payload, gh, event)
