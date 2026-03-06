import pytest

from autotester.AutotesterConfig import AutotesterConfig, E2EConfig


def test_from_yaml_without_workspaces_converts_e2e():
    yaml_content = {
        "name": "TestWorkspace",
        "path": "/tmp/test",
        "ignore": ["*.tmp"],
        "e2e": {
            "login": {"url": "http://example.com", "steps": ["step1", "step2"]},
        },
    }
    config = AutotesterConfig.from_yaml(yaml_content)
    assert config.name == "TestWorkspace"
    assert config.path == "/tmp/test"
    assert config.ignore == ["*.tmp"]
    assert isinstance(config.e2e, E2EConfig)
    assert "login" in config.e2e.tests
    assert config.e2e.tests["login"].url == "http://example.com"


def test_from_yaml_with_workspaces_selects_workspace():
    yaml_content = {
        "workspaces": {
            "ws1": {"name": "Workspace1", "path": "/tmp/ws1"},
            "ws2": {
                "name": "Workspace2",
                "path": "/tmp/ws2",
                "e2e": {
                    "checkout": {
                        "url": "http://example.org",
                        "steps": ["stepA", "stepB"],
                    }
                },
            },
        }
    }
    config = AutotesterConfig.from_yaml(yaml_content, workspace_name="ws2")
    assert config.name == "Workspace2"
    assert config.path == "/tmp/ws2"
    assert isinstance(config.e2e, E2EConfig)
    assert config.e2e.tests["checkout"].steps == ["stepA", "stepB"]


def test_from_yaml_with_workspaces_requires_workspace_name():
    yaml_content = {"workspaces": {"ws1": {"name": "Workspace1"}}}
    with pytest.raises(ValueError, match="workspace_name is required"):
        AutotesterConfig.from_yaml(yaml_content)
