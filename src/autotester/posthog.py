"""
Optional Posthog session replay integration.

When the website under test has Posthog with session replay enabled,
this module can extract the session ID from the browser and generate
a shareable recording link via the Posthog API.
"""

import os
import logging
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger("autotester")

POSTHOG_API_KEY_ENV = "POSTHOG_PERSONAL_API_KEY"


@dataclass
class PosthogConfig:
    project_id: str
    host: str = "https://us.posthog.com"
    personal_api_key: str = ""

    def __post_init__(self):
        self.host = self.host.rstrip("/")
        if not self.personal_api_key:
            self.personal_api_key = os.getenv(POSTHOG_API_KEY_ENV, "")

    @property
    def is_valid(self) -> bool:
        return bool(self.project_id and self.personal_api_key)


def resolve_posthog_config(yaml_config: dict | None) -> PosthogConfig | None:
    """Build a PosthogConfig from the YAML posthog block, if present and valid."""
    if not yaml_config:
        return None

    project_id = str(yaml_config.get("project_id", ""))
    if not project_id:
        logger.warning("posthog.project_id is required; skipping Posthog integration")
        return None

    config = PosthogConfig(
        project_id=project_id,
        host=yaml_config.get("host", "https://us.posthog.com"),
    )

    if not config.is_valid:
        logger.warning(
            f"{POSTHOG_API_KEY_ENV} env var is not set; skipping Posthog integration"
        )
        return None

    return config


async def extract_session_id(browser) -> str | None:
    """
    Execute JS in the current browser page to retrieve the Posthog session ID.
    Returns None if Posthog is not present on the page or extraction fails.
    """
    try:
        page = await browser.get_current_page()
        session_id = await page.evaluate(
            "() => window.posthog ? window.posthog.getSessionId() : null"
        )
        if session_id:
            logger.debug(f"Posthog session ID captured: {session_id}")
        else:
            logger.debug("Posthog SDK not found on page or no active session")
        return session_id
    except Exception as e:
        logger.debug(f"Could not extract Posthog session ID: {e}")
        return None


async def get_recording_url(config: PosthogConfig, session_id: str) -> str | None:
    """
    Enable sharing for a Posthog session recording and return the shareable URL.
    Uses PATCH to enable sharing, then constructs the public replay link.
    """
    sharing_url = (
        f"{config.host}/api/projects/{config.project_id}"
        f"/session_recordings/{session_id}/sharing"
    )
    headers = {
        "Authorization": f"Bearer {config.personal_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                sharing_url,
                json={"enabled": True},
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    access_token = data.get("access_token")
                    if access_token:
                        url = f"{config.host}/shared/{access_token}"
                        logger.debug(f"Posthog recording URL: {url}")
                        return url

                logger.warning(
                    f"Posthog sharing API returned status {resp.status} for session {session_id}"
                )
                return None
    except Exception as e:
        logger.warning(f"Failed to generate Posthog recording link: {e}")
        return None
