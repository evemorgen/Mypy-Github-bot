from app.config import RepoOpts, get_repo_configuration


def test_repo_opts_default_values():
    opts = RepoOpts()
    assert opts.starting_points == ["."]
    assert opts.additional_mypy_opts == ""


def test_repo_opts_custom_values():
    custom_values = {"starting_points": ["1", "2"], "additional_mypy_opts": "--mock-flag"}
    opts = RepoOpts(**custom_values)

    assert opts.starting_points == custom_values["starting_points"]
    assert opts.additional_mypy_opts == custom_values["additional_mypy_opts"]


def test_pyproject_toml_not_found():
    assert get_repo_configuration("mock_repo") == RepoOpts()


def test_pyproject_toml_loaded_no_mypy_bot_section(mocker):
    mocker.patch("app.config.toml.load", return_value={"mock": "config"})
    assert get_repo_configuration("mock_repo") == RepoOpts()


def test_pyproject_toml_bogus_values(mocker):
    mocker.patch("app.config.toml.load", return_value={"tool": {"mypy-bot": {"random": "value"}}})
    assert get_repo_configuration("mock_repo") == RepoOpts()


def test_pyproject_toml_valid_section(mocker):
    mocker.patch("app.config.toml.load", return_value={"tool": {"mypy-bot": {"additional_mypy_opts": "--mock-flag"}}})
    assert get_repo_configuration("mock_repo") == RepoOpts(additional_mypy_opts="--mock-flag")
