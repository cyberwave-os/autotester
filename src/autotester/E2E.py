import asyncio
import os
import json
from types import SimpleNamespace
from urllib.parse import urlparse, urlunparse
from browser_use import Agent, Browser, Controller
from browser_use.llm.models import ChatOpenAI
from dotenv import load_dotenv

from .GitUtils import GitUtils
import logging
from pathlib import Path
from .types import End2endTest, TestCase
from .Report import Report
from .posthog import PosthogConfig, extract_session_id, get_recording_url

load_dotenv()

logger = logging.getLogger("autotester")

DEFAULT_MAX_STEPS_PER_TEST_STEP = 5
DEFAULT_MIN_MAX_STEPS = 20
DEFAULT_TIMEOUT_PER_TEST_STEP = 60  # seconds
DEFAULT_MIN_TIMEOUT = 180  # seconds


controller = Controller(output_model=TestCase)


class E2E:
    """
    E2E class for running end2end tests.
    """

    def __init__(
        self,
        tests: dict,
        chrome_instance_path: str = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        auth: dict | None = None,
        posthog_config: PosthogConfig | None = None,
        base_url: str | None = None,
        max_steps: int | None = None,
        timeout: int | None = None,
    ):
        self.tests = tests
        self.chrome_instance_path = chrome_instance_path
        if os.getenv("CHROME_INSTANCE_PATH"):
            self.chrome_instance_path = os.getenv("CHROME_INSTANCE_PATH")
        self.auth = self._resolve_auth(auth)
        self.posthog_config = posthog_config
        self.base_url = self._resolve_base_url(base_url)
        self.max_steps = max_steps
        self.timeout = timeout

    @staticmethod
    def _resolve_auth(auth: dict | None) -> dict | None:
        """Resolve auth config, with env vars taking precedence over YAML values."""
        env_username = os.getenv("AUTOTESTER_AUTH_USERNAME")
        env_password = os.getenv("AUTOTESTER_AUTH_PASSWORD")

        if env_username and env_password:
            return {"username": env_username, "password": env_password}

        if auth and auth.get("username") and auth.get("password"):
            return {"username": auth["username"], "password": auth["password"]}

        if env_username or env_password:
            logger.warning(
                "Both AUTOTESTER_AUTH_USERNAME and AUTOTESTER_AUTH_PASSWORD must be set; ignoring partial auth config"
            )

        return None

    @staticmethod
    def _resolve_base_url(base_url: str | None) -> str | None:
        """Resolve the base URL, with AUTOTESTER_BASE_URL env var taking precedence."""
        env_base = os.getenv("AUTOTESTER_BASE_URL")
        return env_base if env_base else base_url

    @staticmethod
    def _resolve_url(test_url: str, base_url: str | None) -> str:
        """Combine a test URL with a base URL when the test URL is relative.

        A URL is considered absolute if it contains a scheme (e.g. ``http://``
        or ``https://``).  Everything else is treated as a relative path and
        joined onto *base_url*.  When *base_url* is ``None`` the test URL is
        returned unchanged.
        """
        if base_url is None or "://" in test_url:
            return test_url
        base = base_url.rstrip("/")
        path = test_url if test_url.startswith("/") else f"/{test_url}"
        return f"{base}{path}"

    @staticmethod
    def _apply_basic_auth_to_url(url: str, username: str, password: str) -> str:
        """Embed HTTP Basic Auth credentials into a URL for browser-level auth."""
        parsed = urlparse(url if "://" in url else f"http://{url}")
        authed = parsed._replace(netloc=f"{username}:{password}@{parsed.hostname}"
                                 + (f":{parsed.port}" if parsed.port else ""))
        return urlunparse(authed)

    async def run(self) -> list[End2endTest]:
        all_tests: list[End2endTest] = []
        GitUtils.ensure_autotester_folder_exists_and_in_gitignore()
        for test_name, test in self.tests.items():
            logger.debug(f"Running E2E: {test_name}")
            resolved_url = self._resolve_url(test["url"], self.base_url)
            test_max_steps = test.get("max_steps", self.max_steps)
            test_timeout = test.get("timeout", self.timeout)
            test = End2endTest(
                name=test_name,
                steps=test["steps"],
                url=resolved_url,
            )
            test_result, recording_url = await self.run_test(
                test, max_steps=test_max_steps, timeout=test_timeout
            )
            test.passed = not test_result.failure
            test.errored = test_result.errored
            test.comment = test_result.comment
            test.recording_url = recording_url
            all_tests.append(test)
        # write the results to e2e.json. this is temporary, we will eventually use the report class
        with open(Path.cwd() / ".autotester/e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        # Keep a top-level copy for backward compatibility with older integrations/tests.
        with open(Path.cwd() / "e2e.json", "w") as f:
            json.dump([test.model_dump() for test in all_tests], f)
        report = Report()
        report.add_e2e_results(all_tests)
        with open(Path.cwd() / ".autotester/e2e.xml", "w") as f:
            f.write(report.generate_xml_report())
        passed_count = sum(1 for test in all_tests if test.passed)
        print(f"{passed_count}/{len(all_tests)} E2E tests passed")
        return all_tests

    async def run_test(
        self,
        test: End2endTest,
        max_steps: int | None = None,
        timeout: int | None = None,
    ) -> tuple[TestCase, str | None]:
        GitUtils.ensure_autotester_folder_exists_and_in_gitignore()  # avoid committing logs, screenshots and so on

        effective_max_steps = max_steps or max(
            len(test.steps) * DEFAULT_MAX_STEPS_PER_TEST_STEP,
            DEFAULT_MIN_MAX_STEPS,
        )
        effective_timeout = timeout or max(
            len(test.steps) * DEFAULT_TIMEOUT_PER_TEST_STEP,
            DEFAULT_MIN_TIMEOUT,
        )

        nav_url = test.url
        if self.auth:
            nav_url = self._apply_basic_auth_to_url(
                test.url, self.auth["username"], self.auth["password"]
            )

        try:
            browser = Browser(
                executable_path=self.chrome_instance_path,
                record_video_dir=Path.cwd() / ".autotester/",
                traces_dir=Path.cwd() / ".autotester/",
            )
        except TypeError:
            browser = Browser(
                config=SimpleNamespace(chrome_instance_path=self.chrome_instance_path)
            )

        agent_kwargs: dict = dict(
            task=f"""You are a QA tester. Follow these instructions to perform the test called {test.name}:
* Go to {nav_url}
"""
            + "\n".join(f"* {step}" for step in test.steps)
            + "\n\nIf any step that starts with 'Check' fails, the result is a failure",
            llm=ChatOpenAI(model="gpt-4o"),
            controller=controller,
            browser=browser,
        )

        if self.auth:
            agent_kwargs["extend_system_message"] = (
                "This site uses HTTP Basic Authentication. "
                "Credentials are already embedded in the URL. "
                "If you encounter a 401 or authentication prompt, "
                "re-navigate to the URL which already contains the credentials."
            )

        agent = Agent(**agent_kwargs)

        timed_out = False
        try:
            history = await asyncio.wait_for(
                agent.run(max_steps=effective_max_steps),
                timeout=effective_timeout,
            )
        except asyncio.TimeoutError:
            timed_out = True
            logger.warning(
                "Test '%s' timed out after %ds", test.name, effective_timeout
            )

        session_id = None
        if self.posthog_config:
            session_id = await extract_session_id(browser)

        if hasattr(browser, "stop"):
            await browser.stop()
        elif hasattr(browser, "close"):
            await browser.close()

        if timed_out:
            test_result = TestCase(
                failure=True,
                comment=f"Test timed out after {effective_timeout}s",
                errored=True,
            )
        elif result := history.final_result():
            result_data = json.loads(result)
            if "failure" not in result_data and "passed" in result_data:
                result_data["failure"] = not bool(result_data["passed"])
            test_result: TestCase = TestCase.model_validate(result_data)
        else:
            test_result = TestCase(
                failure=True,
                comment="No result from the test",
                errored=True,
            )

        recording_url = None
        if self.posthog_config and session_id and test_result.failure:
            recording_url = await get_recording_url(self.posthog_config, session_id)

        return test_result, recording_url
