import asyncio
import sys
import traceback
import logging

import aiohttp
from aiohttp import web
import cachetools
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing
from gidgethub import sansio

from app.git_operations import clone_repo
from app.mypy_adapter import perform_mypy_thing

from app import config

logger = logging.getLogger(__name__)


router = routing.Router()
LRU_CACHE = cachetools.LRUCache(maxsize=500)
routes = web.RouteTableDef()


@routes.post("/webhook")
async def webhook(request):
    try:
        body = await request.read()
        secret = config.GH_SECRET
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(session, "mypy-thing", cache=LRU_CACHE)

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
    return await perform_mypy_thing(event, gh)


@router.register("pull_request", action="synchronize")
async def on_push(event, gh, *args, **kwargs):
    return await perform_mypy_thing(event, gh)


@router.register("installation", action="created")
async def repo_installation_added(event, gh, *args, **kwargs):
    for repository in event.data["repositories"]:
        repo_name = repository["full_name"]
        await clone_repo(repo_name, gh, event)


app = web.Application()
app.router.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, port=config.PORT)