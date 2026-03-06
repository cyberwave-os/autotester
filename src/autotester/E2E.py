import os
import json
from types import SimpleNamespace
from browser_use import Agent, Browser, Controller
from browser_use.llm.models import ChatOpenAI
from dotenv import load_dotenv

from .GitUtils import GitUtils
import logging
from pathlib import Path
from .types import End2endTest, TestCase
from .Report import Report

load_dotenv()

logger = logging.getLogger("autotester")


controller = Controller(output_model=TestCase)


class E2E:
    """
    E2E class for running end2end tests.
    """

    def __init__(
        self,
        tests: dict,
        chrome_instance_path: str = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        self.tests = tests
        self.chrome_instance_path = chrome_instance_path
        if os.getenv("CHROME_INSTANCE_PATH"):
            self.chrome_instance_path = os.getenv("CHROME_INSTANCE_PATH")

    async def run(self) -> list[End2endTest]:
        all_tests: list[End2endTest] = []
        GitUtils.ensure_autotester_folder_exists_and_in_gitignore()
        for test_name, test in self.tests.items():
            logger.debug(f"Running E2E: {test_name}")
            test = End2endTest(
                name=test_name,
                steps=test["steps"],
                url=test["url"],
            )
            test_result = await self.run_test(test)
            test.passed = not test_result.failure
            test.errored = test_result.errored
            test.comment = test_result.comment
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

    async def run_test(self, test: End2endTest) -> TestCase:
        GitUtils.ensure_autotester_folder_exists_and_in_gitignore()  # avoid committing logs, screenshots and so on
        try:
            browser = Browser(
                # NOTE: you need to close your chrome browser - so this can connect to your desired executable
                executable_path=self.chrome_instance_path,
                record_video_dir=Path.cwd() / ".autotester/",
                traces_dir=Path.cwd() / ".autotester/",
            )
        except TypeError:
            # Backward-compatible path for tests/mocks expecting Browser(config=...)
            browser = Browser(
                config=SimpleNamespace(chrome_instance_path=self.chrome_instance_path)
            )
        agent = Agent(
            task=f"""You are a QA tester. Follow these instructions to perform the test called {test.name}:
* Go to {test.url}
"""
            + "\n".join(f"* {step}" for step in test.steps)
            + "\n\nIf any step that starts with 'Check' fails, the result is a failure",
            llm=ChatOpenAI(model="gpt-4o"),
            controller=controller,
            browser=browser,
        )
        history = await agent.run()
        if hasattr(browser, "stop"):
            await browser.stop()
        elif hasattr(browser, "close"):
            await browser.close()
        result = history.final_result()
        if result:
            result_data = json.loads(result)
            if "failure" not in result_data and "passed" in result_data:
                # Accept legacy/alternative output schema that uses "passed"
                result_data["failure"] = not bool(result_data["passed"])
            test_result: TestCase = TestCase.model_validate(result_data)
            return test_result
        else:
            return TestCase(
                failure=True,
                comment="No result from the test",
                errored=True,
            )
