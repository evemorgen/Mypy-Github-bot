import os
import subprocess

from git import Repo



def generate_repo_url(access_token, repo_name):
    return f"https://x-access-token:{access_token}@github.com/{repo_name}.git"

token = "v1.d4adca5698e7312598695eda50c39a037392e3ba"
repo_name = "evemorgen/cmb-events"


if not os.path.exists(f"./{repo_name}"):
    repo = Repo()
    repo.clone_from(url=generate_repo_url(token, repo_name), to_path=f"./{repo_name}")
else:
    repo = Repo(f"./{repo_name}")


print(generate_repo_url(token, repo_name))

#_git = repo.git

#repo.remotes.origin.fetch()


#_git.checkout("wip")
subprocess.run(["bash", "-c", f"cd ./{repo_name}/ && git fetch --all"])
subprocess.run(["bash", "-c", f"cd ./{repo_name}/ && git checkout wip"])
result = subprocess.run(["mypy", f"./{repo_name}/."], capture_output=True)
from pprint import pprint
first = set(result.stdout.decode().split("\n"))
#_git.checkout("analytics-in-ops")
subprocess.run(["bash", "-c", f"cd ./{repo_name}/ && git checkout dupa"])
result = subprocess.run(["mypy", f"./{repo_name}/."], capture_output=True)
print("===================")
second = set(result.stdout.decode().split("\n"))
print("===================")
#_git.checkout("wip")
print(second - first)

