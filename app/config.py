import os

REPOS_PREFIX = "."  # local devel
# REPOS_PREFIX = "/app" # heroku

GH_SECRET = os.environ["GH_SECRET"]
GH_APP_ID = os.environ["GH_APP_ID"]
GH_PRIVATE_KEY = os.environ["GH_PRIVATE_KEY"]
GH_REVIEW_USER = 64769253
PORT = int(os.environ.get("PORT", 3000))

MYPY_ADDITIONAL_ARGS = "--ignore-missing-imports"
