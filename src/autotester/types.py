from enum import Enum
from pydantic import BaseModel


class TestErrorType(Enum):
    TEST = "test"  # this means the test is not written correctly
    BUG = "bug"  # this means the code that is being tested is not written correctly
    SETTINGS = "settings"  # this means the test settings are not configured correctly


class End2endTest(BaseModel):
    steps: list[str]
    url: str
    passed: bool = False
    errored: bool = False
    comment: str = ""
    name: str
    recording_url: str | None = None
    video_path: str | None = None
    """Filesystem path (relative to the project root) to an MP4 recording of
    the test run, when video recording is enabled. ``None`` if no video was
    produced (e.g. the optional ``browser-use[video]`` extra is missing or
    recording was disabled)."""

    def __init__(self, name: str, steps: list[str], url: str):
        super().__init__(name=name, steps=steps, url=url)


class TestCase(BaseModel):
    failure: bool
    comment: str
    errored: bool = False

    @property
    def passed(self) -> bool:
        """Compatibility alias used by older tests/callers."""
        return not self.failure
