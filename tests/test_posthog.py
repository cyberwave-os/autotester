"""Tests for the optional Posthog session replay integration."""

import pytest

from autotester.posthog import (
    PosthogConfig,
    resolve_posthog_config,
    extract_session_id,
    get_recording_url,
    POSTHOG_API_KEY_ENV,
)


# ---------------------------------------------------------------------------
# PosthogConfig
# ---------------------------------------------------------------------------

class TestPosthogConfig:
    def test_defaults(self):
        config = PosthogConfig(project_id="123", personal_api_key="phx_key")
        assert config.host == "https://us.posthog.com"
        assert config.is_valid is True

    def test_trailing_slash_stripped(self):
        config = PosthogConfig(
            project_id="123",
            host="https://eu.posthog.com/",
            personal_api_key="phx_key",
        )
        assert config.host == "https://eu.posthog.com"

    def test_invalid_without_api_key(self, monkeypatch):
        monkeypatch.delenv(POSTHOG_API_KEY_ENV, raising=False)
        config = PosthogConfig(project_id="123")
        assert config.is_valid is False

    def test_invalid_without_project_id(self):
        config = PosthogConfig(project_id="", personal_api_key="phx_key")
        assert config.is_valid is False

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv(POSTHOG_API_KEY_ENV, "phx_from_env")
        config = PosthogConfig(project_id="456")
        assert config.personal_api_key == "phx_from_env"
        assert config.is_valid is True

    def test_explicit_key_not_overridden_by_env(self, monkeypatch):
        monkeypatch.setenv(POSTHOG_API_KEY_ENV, "phx_from_env")
        config = PosthogConfig(project_id="456", personal_api_key="phx_explicit")
        assert config.personal_api_key == "phx_explicit"


# ---------------------------------------------------------------------------
# resolve_posthog_config
# ---------------------------------------------------------------------------

class TestResolvePosthogConfig:
    def test_none_input(self):
        assert resolve_posthog_config(None) is None

    def test_empty_dict(self):
        assert resolve_posthog_config({}) is None

    def test_missing_project_id(self, monkeypatch):
        monkeypatch.setenv(POSTHOG_API_KEY_ENV, "phx_key")
        assert resolve_posthog_config({"host": "https://us.posthog.com"}) is None

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv(POSTHOG_API_KEY_ENV, raising=False)
        assert resolve_posthog_config({"project_id": "123"}) is None

    def test_valid_config(self, monkeypatch):
        monkeypatch.setenv(POSTHOG_API_KEY_ENV, "phx_key")
        config = resolve_posthog_config({
            "project_id": "789",
            "host": "https://eu.posthog.com",
        })
        assert config is not None
        assert config.project_id == "789"
        assert config.host == "https://eu.posthog.com"
        assert config.personal_api_key == "phx_key"

    def test_default_host(self, monkeypatch):
        monkeypatch.setenv(POSTHOG_API_KEY_ENV, "phx_key")
        config = resolve_posthog_config({"project_id": "100"})
        assert config.host == "https://us.posthog.com"

    def test_project_id_coerced_to_string(self, monkeypatch):
        monkeypatch.setenv(POSTHOG_API_KEY_ENV, "phx_key")
        config = resolve_posthog_config({"project_id": 42})
        assert config.project_id == "42"


# ---------------------------------------------------------------------------
# extract_session_id
# ---------------------------------------------------------------------------

class FakePage:
    def __init__(self, return_value=None, raise_error=False):
        self._return_value = return_value
        self._raise_error = raise_error

    async def evaluate(self, script):
        if self._raise_error:
            raise RuntimeError("Page context destroyed")
        return self._return_value


class FakeBrowserWithPage:
    def __init__(self, page):
        self._page = page

    async def get_current_page(self):
        return self._page


class FakeBrowserNoPage:
    async def get_current_page(self):
        raise AttributeError("get_current_page not supported")


@pytest.mark.asyncio
class TestExtractSessionId:
    async def test_returns_session_id(self):
        page = FakePage(return_value="session_abc123")
        browser = FakeBrowserWithPage(page)
        result = await extract_session_id(browser)
        assert result == "session_abc123"

    async def test_returns_none_when_posthog_not_on_page(self):
        page = FakePage(return_value=None)
        browser = FakeBrowserWithPage(page)
        result = await extract_session_id(browser)
        assert result is None

    async def test_returns_none_on_page_error(self):
        page = FakePage(raise_error=True)
        browser = FakeBrowserWithPage(page)
        result = await extract_session_id(browser)
        assert result is None

    async def test_returns_none_when_get_current_page_fails(self):
        browser = FakeBrowserNoPage()
        result = await extract_session_id(browser)
        assert result is None


# ---------------------------------------------------------------------------
# get_recording_url
# ---------------------------------------------------------------------------

class FakeAiohttpResponse:
    def __init__(self, status, data):
        self.status = status
        self._data = data

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeAiohttpSession:
    def __init__(self, response):
        self._response = response

    def patch(self, url, json=None, headers=None):
        self._last_url = url
        self._last_json = json
        self._last_headers = headers
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
class TestGetRecordingUrl:
    async def test_success(self, monkeypatch):
        config = PosthogConfig(
            project_id="123",
            host="https://us.posthog.com",
            personal_api_key="phx_key",
        )
        fake_resp = FakeAiohttpResponse(200, {"access_token": "tok_abc"})
        fake_session = FakeAiohttpSession(fake_resp)

        monkeypatch.setattr(
            "autotester.posthog.aiohttp.ClientSession",
            lambda: fake_session,
        )

        url = await get_recording_url(config, "sess_123")
        assert url == "https://us.posthog.com/shared/tok_abc"
        assert "/api/projects/123/session_recordings/sess_123/sharing" in fake_session._last_url
        assert fake_session._last_json == {"enabled": True}
        assert "Bearer phx_key" in fake_session._last_headers["Authorization"]

    async def test_non_200_response(self, monkeypatch):
        config = PosthogConfig(
            project_id="123",
            host="https://us.posthog.com",
            personal_api_key="phx_key",
        )
        fake_resp = FakeAiohttpResponse(403, {})
        fake_session = FakeAiohttpSession(fake_resp)

        monkeypatch.setattr(
            "autotester.posthog.aiohttp.ClientSession",
            lambda: fake_session,
        )

        url = await get_recording_url(config, "sess_123")
        assert url is None

    async def test_missing_access_token(self, monkeypatch):
        config = PosthogConfig(
            project_id="123",
            host="https://us.posthog.com",
            personal_api_key="phx_key",
        )
        fake_resp = FakeAiohttpResponse(200, {"enabled": True})
        fake_session = FakeAiohttpSession(fake_resp)

        monkeypatch.setattr(
            "autotester.posthog.aiohttp.ClientSession",
            lambda: fake_session,
        )

        url = await get_recording_url(config, "sess_123")
        assert url is None

    async def test_network_error(self, monkeypatch):
        config = PosthogConfig(
            project_id="123",
            host="https://us.posthog.com",
            personal_api_key="phx_key",
        )

        monkeypatch.setattr(
            "autotester.posthog.aiohttp.ClientSession",
            lambda: (_ for _ in ()).throw(ConnectionError("Network down")),
        )

        url = await get_recording_url(config, "sess_123")
        assert url is None

    async def test_custom_host(self, monkeypatch):
        config = PosthogConfig(
            project_id="99",
            host="https://posthog.mycompany.com",
            personal_api_key="phx_self_hosted",
        )
        fake_resp = FakeAiohttpResponse(200, {"access_token": "tok_self"})
        fake_session = FakeAiohttpSession(fake_resp)

        monkeypatch.setattr(
            "autotester.posthog.aiohttp.ClientSession",
            lambda: fake_session,
        )

        url = await get_recording_url(config, "sess_self")
        assert url == "https://posthog.mycompany.com/shared/tok_self"
        assert "posthog.mycompany.com" in fake_session._last_url
