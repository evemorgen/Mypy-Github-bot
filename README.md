Example entry in `pyproject.toml`:
```
[tool.mypy-bot]
starting_points = ["urls.py"]  # if not defined, defaults to "." in repo root directory
additional_mypy_opts = "--ignore-missing-imports --strict-equality" # additional flags to provide to mypy, for list of all available options use `mypy --help`
```