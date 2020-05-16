import asyncio
import os
import sys
import traceback
import subprocess

import aiohttp
from aiohttp import web
import cachetools
from git import Repo
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import sansio
from gidgethub import apps

router = routing.Router()
cache = cachetools.LRUCache(maxsize=500)

routes = web.RouteTableDef()


@routes.get("/", name="home")
async def handle_get(request):
    return web.Response(text="Hello world")


@routes.post("/webhook")
async def webhook(request):
    try:
        body = await request.read()
        secret = os.environ.get("GH_SECRET")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(session, "demo", cache=cache)

            await asyncio.sleep(1)
            await router.dispatch(event, gh)
        try:
            print("GH requests remaining:", gh.rate_limit.remaining)
        except AttributeError:
            pass
        return web.Response(status=200)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return web.Response(status=500)


@router.register("pull_request", action="opened")
async def pr_opened(event, gh, *args, **kwargs):
    installation_id = event.data["installation"]["id"]
    installation_access_token = await apps.get_installation_access_token(
        gh,
        installation_id=installation_id,
        app_id=os.environ.get("GH_APP_ID"),
        private_key=os.environ.get("GH_PRIVATE_KEY")
    )

    pr_root = event.data["pull_request"]
    print(pr_root)
    branch_from, branch_to = pr_root["head"]["ref"], pr_root["base"]["ref"]
    print(f"to: {branch_to}")
    print(f"from: {branch_from}")
    repo_name = event.data["repository"]["full_name"]

    if not os.path.exists(f"/app/{repo_name}"):
        Repo.clone_from(url=generate_repo_url(installation_access_token["token"], repo_name), to_path=f"/app/{repo_name}")

    repo = Repo(f"/app/{repo_name}")
    git = repo.git

    git.fetch(all=True)
    git.checkout(branch_to)
    result = subprocess.run(["mypy", f"./{repo_name}/."], capture_output=True)

    first = set(result.stdout.decode().split("\n"))

    git.checkout(branch_from)
    result = subprocess.run(["mypy", f"./{repo_name}/."], capture_output=True)
    second = set(result.stdout.decode().split("\n"))
    print(f"diff: {second - first}")

    for event in second - first:
        if event.startswith("Found"):
            continue
        try:
            print(event)
            path, line_no, _, error = event.split(":", maxsplit=3)
            latest_commit_sha = pr_root["head"]["sha"]
            path = path.replace(repo_name, "")
            
            body = {
                "body": error,
                "commit_id": latest_commit_sha,
                "path": path[1:],
                "position": line_no
            }
            print(body)
            url = f"/repos/{repo_name}/pulls/{pr_root['number']}/comments"
            print(url)
            response = await gh.post(
                f"/repos/{repo_name}/pulls/{pr_root['number']}/comments", 
                data=body
            )
            print(response)
        except Exception:
            pass


def generate_repo_url(access_token, repo_name):
    return f"https://x-access-token:{access_token}@github.com/{repo_name}.git"


@router.register("installation", action="created")
async def repo_installation_added(event, gh, *args, **kwargs):
    installation_id = event.data["installation"]["id"]
    installation_access_token = await apps.get_installation_access_token(
        gh,
        installation_id=installation_id,
        app_id=os.environ.get("GH_APP_ID"),
        private_key=os.environ.get("GH_PRIVATE_KEY")
    )

    for repository in event.data['repositories']:
        repo_name = repository["full_name"]
        if not os.path.exists(f"/app/{repo_name}"):
            Repo.clone_from(url=generate_repo_url(installation_access_token["token"], repo_name), to_path=f"/app/{repo_name}")

        repo = Repo(f"/app/{repo_name}")
        print(os.listdir("./app/"))


if __name__ == "__main__":  # pragma: no cover
    app = web.Application()

    app.router.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)
