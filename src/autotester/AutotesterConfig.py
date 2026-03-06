from dataclasses import dataclass


@dataclass
class E2ETestConfig:
    """
    Represents a single E2E test configuration
    """

    url: str
    steps: list[str]


@dataclass
class E2EConfig:
    """
    Represents the E2E testing configuration section
    """

    tests: dict[str, E2ETestConfig]

    @staticmethod
    def from_dict(data: dict) -> "E2EConfig":
        tests = {
            name: E2ETestConfig(**test_config) for name, test_config in data.items()
        }
        return E2EConfig(tests=tests)


@dataclass
class AutotesterConfig:
    """
    Represents a workspace configuration as defined in autotester.yml
    """

    name: str | None = None
    path: str | None = None
    ignore: list[str] | None = None
    e2e: E2EConfig | None = None

    def __init__(self, **kwargs):
        # Initialize with provided kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Always convert e2e config to E2EConfig if it's a dictionary
        if hasattr(self, "e2e") and self.e2e is not None and isinstance(self.e2e, dict):
            self.e2e = E2EConfig.from_dict(self.e2e)

    @staticmethod
    def from_yaml(
        yaml_content: dict, workspace_name: str | None = None
    ) -> "AutotesterConfig":
        if "workspaces" in yaml_content:
            if not workspace_name:
                raise ValueError(
                    "workspace_name is required when workspaces are defined"
                )
            if workspace_name not in yaml_content["workspaces"]:
                raise ValueError(f"workspace {workspace_name} not found in workspaces")
            return AutotesterConfig(**yaml_content["workspaces"][workspace_name])
        else:
            return AutotesterConfig(**yaml_content)
