from app.config import RepoOpts
from app.mypy_adapter import (
    MypyError,
    if_error_in_hunk,
    parse_mypy_output,
    perform_mypy_check,
)
from unidiff import Hunk


def test_mypy_output_parsing():
    output_lines = [
        "app/mypy_adapter.py:21: error: Skipping analyzing 'unidiff': found module but no type hints or library stubs",
        "tests/test_events.py:28: error: Need type annotation for 'records' (hint: \"records: Dict[<type>, <type>] = ...\")",
    ]

    parsed_errors = parse_mypy_output(output_lines)
    assert len(parsed_errors) == 2
    assert all(isinstance(err, MypyError) for err in parsed_errors)
    dict_error = parsed_errors[1]
    assert dict_error.line_no == 28 and dict_error.severity == "error" and dict_error.file == "tests/test_events.py"


def test_parse_output_skip_cases():
    output_lines = [
        # errors summary, skip that
        "Found 6 errors in 4 files (checked 5 source files)",
        # crossed out comment from github, also skip that
        "~~app/mypy_adapter.py:21: error: Skipping analyzing 'unidiff': found module but no type hints or library stubs~~",
    ]

    parsed_errors = parse_mypy_output(output_lines)
    assert len(parsed_errors) == 0


def test_mypy_error_eq_line_no_differs():
    matching_opts = {"file": "mock_file.py", "error_body": "mock error body", "severity": "error"}
    MypyError(**matching_opts, line_no=42) == MypyError(**matching_opts, line_no=7)


def test_parse_mypy_error_str():
    mypy_error_str = "file:10:severity:body-with-colon:in:the:middle"
    parsed_error = parse_mypy_output([mypy_error_str])[0]

    assert str(parsed_error) == mypy_error_str


def test_perform_mypy_check_default_case(mocker):
    subprocess_mock = mocker.patch("app.mypy_adapter.subprocess.run")
    subprocess_mock.return_value.stdout = b"mock\nlines\n"

    result = perform_mypy_check("mock-repo")

    assert result == {"mock", "lines"}
    assert " ".join(subprocess_mock.call_args[0][0]) == "mypy  ."
    assert subprocess_mock.call_args[1]["cwd"] == "./mock-repo"


def test_perform_mypy_check_custom_opts_multiple_files(mocker):
    mocker.patch(
        "app.mypy_adapter.get_repo_configuration",
        return_value=RepoOpts(starting_points=["urls.py", "main.py"], additional_mypy_opts="--mock-flag"),
    )
    subprocess_mock = mocker.patch("app.mypy_adapter.subprocess.run")
    subprocess_mock.return_value.stdout = b"mock\nlines\n"

    result = perform_mypy_check("mock-repo")

    assert result == {"mock", "lines"}
    assert " ".join(subprocess_mock.call_args[0][0]) == "mypy --mock-flag urls.py main.py"
    assert subprocess_mock.call_args[1]["cwd"] == "./mock-repo"


def test_error_in_hunk():
    hunk = Hunk(src_start=7, src_len=10, tgt_start=9, tgt_len=10)
    error = MypyError(file="mock-file", line_no=18, severity="err", error_body="err")

    assert if_error_in_hunk(error, hunk) is True


def test_error_not_in_hunk():
    hunk = Hunk(src_start=7, src_len=10, tgt_start=9, tgt_len=10)
    error = MypyError(file="mock-file", line_no=23, severity="err", error_body="err")

    assert if_error_in_hunk(error, hunk) is False
