import os
import subprocess

from git import Repo



def generate_repo_url(access_token, repo_name):
    return f"https://x-access-token:{access_token}@github.com/{repo_name}.git"

token = "v1.69f278f09aedc2f718acf6441f1070b8041a8079"
repo_name = "evemorgen/cmb-events"


if not os.path.exists(f"./{repo_name}"):
    repo = Repo()
    repo.clone_from(url=generate_repo_url(token, repo_name), to_path=f"./{repo_name}")
else:
    repo = Repo(f"./{repo_name}")


breakpoint()

print(generate_repo_url(token, repo_name))

#_git = repo.git

#repo.remotes.origin.fetch()


#_git.checkout("wip")
subprocess.run(["bash", "-c", f"cd ./{repo_name}/ && git fetch --all"])
subprocess.run(["bash", "-c", f"cd ./{repo_name}/ && git checkout wip"])
result = subprocess.run(["mypy", f"./{repo_name}/."], capture_output=True)
from pprint import pprint
first = set(result.stdout.decode().split("\n"))
print("first: %s" % first)
#_git.checkout("analytics-in-ops")
subprocess.run(["bash", "-c", f"cd ./{repo_name}/ && git checkout dupa"])
result = subprocess.run(["mypy", f"./{repo_name}/."], capture_output=True)
print("===================")
second = set(result.stdout.decode().split("\n"))
print("second: %s" % second)
print("===================")
#_git.checkout("wip")
print("diff: %s" % (second - first))
