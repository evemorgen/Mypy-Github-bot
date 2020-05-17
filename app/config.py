import os


REPOS_PREFIX = "."  # local devel
# REPOS_PREFIX = "/app" # heroku

GH_SECRET = os.environ.get("GH_SECRET")
GH_APP_ID = os.environ.get("GH_APP_ID")
GH_PRIVATE_KEY = os.environ.get("GH_PRIVATE_KEY")
PORT = int(os.environ.get("PORT", 3000))
