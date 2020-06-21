Example entry in `pyproject.toml`:
```
[tool.mypy-bot]
starting_points = ["urls.py"]  # if not defined, defaults to "." in repo root directory
use_mypy_ini = false  # by default mypy-bot tries to use mypy.ini if defined in repo root direcotry
additional_mypy_opts = "--ignore-missing-imports --strict-equality" # additional flags to provide to mypy, for list of all available options use `mypy --help`
```