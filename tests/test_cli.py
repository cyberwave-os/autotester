"""CLI tests for the current E2E-only Autotester interface."""

from pathlib import Path
import pytest

from autotester import cli, __version__


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "REPLACEME")


def _write_config(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"Autotester {__version__}" in captured.out


def test_help():
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])
    assert exc_info.value.code == 0


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["e2e"])
    assert exc_info.value.code == 1


def test_e2e_command_dispatches_to_runner(tmp_path, monkeypatch, mock_env):
    config_file = _write_config(
        tmp_path / "autotester.yml",
        "e2e:\n  smoke:\n    url: 'http://example.com'\n    steps:\n      - Check homepage\n",
    )
    called = {"value": False}

    def fake_run_e2e_command(args):
        called["value"] = True
        assert args.yaml_file == str(config_file)
        raise SystemExit(0)

    monkeypatch.setattr(cli, "run_e2e_command", fake_run_e2e_command)
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["e2e", "--config", str(config_file)])
    assert exc_info.value.code == 0
    assert called["value"] is True


def test_default_mode_runs_when_e2e_present(tmp_path, monkeypatch, mock_env):
    _write_config(
        tmp_path / "autotester.yml",
        "e2e:\n  smoke:\n    url: 'http://example.com'\n    steps:\n      - Check homepage\n",
    )
    monkeypatch.chdir(tmp_path)

    def fake_run_e2e_command(args):
        assert args.yaml_file == "autotester.yml"
        raise SystemExit(0)

    monkeypatch.setattr(cli, "run_e2e_command", fake_run_e2e_command)
    with pytest.raises(SystemExit) as exc_info:
        cli.main([])
    assert exc_info.value.code == 0


def test_default_mode_errors_when_no_e2e_config(tmp_path, monkeypatch, mock_env):
    _write_config(tmp_path / "autotester.yml", "name: sample\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        cli.main([])
    assert exc_info.value.code == 1
