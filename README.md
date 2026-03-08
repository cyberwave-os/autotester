# Autotester

[![GitHub license](https://img.shields.io/badge/License-MIT-orange.svg)](https://github.com/cyberwaveos/autotester/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=orange)](https://discord.gg/4QMwWdsMGt)
[![Documentation](https://img.shields.io/badge/Documentation-📖-orange)](https://docs.autotester.com)
<a href="https://github.com/cyberwaveos/autotester/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/cyberwaveos/autotester/main?style=for-the-badge" height="20">
</a><br>

Autotester is an open-source testing automation tool to make E2E automated.

- 🤖 **Run end-to-end tests** using natural language descriptions
- 🐛 **Detect potential bugs** and provide detailed fix explanations
- ⚡ **Reduce testing overhead** while improving code quality

Currently supporting Python and TypeScript, with more languages coming soon.

## Quickstart

Install the package

```bash
pip install autotester
```

Add a config file to your project called `autotester.yml`. This tells Autotester what to test and how.

```yaml
e2e:
  login-test: # Name of the test. You can add more
    url: "localhost:3000" # Starting URL of your app. It can be a local server or a remote server
    steps:
      - Login with Github
      - Go to the team page
      - Change the team name to "e2e"
      - Click on the "Save" button
      - Check that the team name is "e2e" # use words like "Check that" to assert the results of the test
```

If your environment is protected by **HTTP Basic Auth**, add an `auth` block:

```yaml
e2e:
  auth:
    type: basic
    username: "dev"
    password: "dev123"
  login-test:
    url: "https://staging.example.com"
    steps:
      - Check the homepage loads
```

You can also provide auth credentials via environment variables (these take precedence over YAML):

```bash
export AUTOTESTER_AUTH_USERNAME="dev"
export AUTOTESTER_AUTH_PASSWORD="dev123"
```

### Posthog Session Replay (Optional)

If your website uses [Posthog](https://posthog.com) with [session replay](https://posthog.com/docs/session-replay) enabled, Autotester can capture a recording of each failed test and include a direct link in the report. This makes it easy for QA engineers to watch exactly what happened during a failure.

Add a `posthog` block to your `autotester.yml`:

```yaml
e2e:
  posthog:
    project_id: "12345" # Your Posthog project ID (found in Project Settings)
    host: "https://us.posthog.com" # Optional, defaults to https://us.posthog.com
  login-test:
    url: "localhost:3000"
    steps:
      - Login with Github
      - Check that the dashboard loads
```

Then set the `POSTHOG_PERSONAL_API_KEY` environment variable. The key needs the `session_recording:read` and `sharing_configuration:write` scopes. You can create one in your [Posthog personal API keys settings](https://us.posthog.com/settings/user-api-keys).

```bash
export POSTHOG_PERSONAL_API_KEY="phx_your_personal_api_key"
```

When a test fails, the report will include a link to the Posthog recording:

```bash
login-test: Failed!
  Comment: The dashboard did not load after login
  Recording: https://us.posthog.com/shared/abc123token
```

**How it works:** When Autotester's browser navigates your website, the Posthog JS SDK (already running in the page) records the session automatically. After each test, Autotester reads the session ID from the page via `posthog.getSessionId()`. If the test failed, it calls the Posthog API to enable sharing for that recording and includes the resulting link in the report. No extra code or instrumentation is needed on your website beyond having Posthog installed.

**Self-hosted / EU Cloud:** Set `host` to your Posthog instance URL (e.g. `https://eu.posthog.com` or `https://posthog.yourcompany.com`).

**Finding your project ID:** Go to your [Posthog project settings](https://us.posthog.com/settings/project) -- the project ID is shown at the top of the page.

### Base URL (Optional)

If you use the same `autotester.yml` across different environments (e.g. staging, production) that share the same relative paths but have different hostnames, you can set a **base URL**. Test URLs that are relative (no `http://` or `https://` scheme) will be combined with the base URL automatically. Absolute test URLs are always used as-is.

Add a `base_url` to your `autotester.yml`:

```yaml
e2e:
  base_url: "https://staging.example.com"
  login-test:
    url: "/login"       # resolved to https://staging.example.com/login
    steps:
      - Check the login page loads
  dashboard-test:
    url: "/dashboard"   # resolved to https://staging.example.com/dashboard
    steps:
      - Check the dashboard loads
```

You can also (or instead) set the base URL via an environment variable, which takes precedence over the YAML value:

```bash
export AUTOTESTER_BASE_URL="https://production.example.com"
```

This makes it easy to reuse the same config file across environments:

```bash
# staging
AUTOTESTER_BASE_URL="https://staging.example.com" autotester

# production
AUTOTESTER_BASE_URL="https://production.example.com" autotester
```

Tests with absolute URLs (e.g. `url: "https://other-service.com/health"`) are never modified, regardless of the base URL setting.

---

That's it. To run it, you need to have an OpenAI API key and Chrome/Chromium installed.

If you don't already have Chrome installed, you can use the [browser-use](https://github.com/browser-use/browser-use) CLI to install Chromium:

```bash
browser-use install
```

Then export your OpenAI key and run:

```bash
export OPENAI_API_KEY="your-openai-api-key"
autotester
```

You will get a summary report like the following:

```bash

🖥️ 1/1 E2E tests

login-test: Success!
```

## GitHub Action

Autotester can be used in a [GitHub Action](https://github.com/cyberwave-os/autotester-action) to run E2E tests after you release a new version.

Check out the action's [README](https://github.com/cyberwave-os/autotester-action/blob/main/README.md) for more information, but here's a quick example:

```yaml
name: Run Autotester

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  after-deployment:
    runs-on: ubuntu-latest
    steps:
      - uses: cyberwave-os/autotester-action@v0.1.0
        with:
          action-type: "e2e"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          STARTING_URL: "http://yourstaging.yourwebsite.com"
          # Optional: override base URL for this environment
          # AUTOTESTER_BASE_URL: "https://staging.yourwebsite.com"
          # Optional: for Basic Auth protected environments
          # AUTOTESTER_AUTH_USERNAME: ${{ secrets.AUTOTESTER_AUTH_USERNAME }}
          # AUTOTESTER_AUTH_PASSWORD: ${{ secrets.AUTOTESTER_AUTH_PASSWORD }}
```

### With Posthog Session Replay

If your website uses Posthog, you can get recording links for failed tests. Add a `posthog` block to your `autotester.yml` (see the [Posthog section above](#posthog-session-replay-optional)) and pass the API key:

```yaml
name: Autotester E2E with Posthog Replay

on:
  pull_request:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Autotester E2E Tests
        uses: cyberwave-os/autotester-action@v0.1.0
        with:
          action-type: "e2e"
          verbose: "true"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          POSTHOG_PERSONAL_API_KEY: ${{ secrets.POSTHOG_PERSONAL_API_KEY }}
```

The recording URL appears in the console output and is also available in `.autotester/e2e.json` (as `recording_url` on each test) for use in downstream steps like Slack notifications or PR comments.

## CLI Reference

### Commands

- `autotester`: Without any command, runs E2E tests if defined in autotester.yml
- `autotester e2e`: Runs end-to-end tests defined in autotester.yml

### Command Options

#### Global Options

- `-v, --verbose`: Enable verbose logging output
- `--version`: Display Autotester version number

#### E2E Test Command

```bash
autotester e2e [--config <config_file>] [--verbose]
```

- `--config`: (Optional) Path to the YAML configuration file (defaults to autotester.yml)
- `-v, --verbose`: (Optional) Enable verbose logging output

### Environment Variables

- `OPENAI_API_KEY`: (Required) Your OpenAI API key
- `CHROME_INSTANCE_PATH`: Path to your Chrome instance. Defaults to `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- `AUTOTESTER_BASE_URL`: Base URL to combine with relative test URLs (overrides `base_url` in YAML)
- `AUTOTESTER_AUTH_USERNAME`: Username for HTTP Basic Auth (overrides `auth.username` in YAML)
- `AUTOTESTER_AUTH_PASSWORD`: Password for HTTP Basic Auth (overrides `auth.password` in YAML)
- `POSTHOG_PERSONAL_API_KEY`: Personal API key for Posthog session replay integration (optional, requires `session_recording:read` and `sharing_configuration:write` scopes)

## Run Tests with Docker

For contributors who want a reproducible test environment, you can run the test suite in Docker.

From the repository root:

```bash
make test-docker
```

This command mounts your local project into the container and runs `pytest`.
If you want to build manually first:

```bash
make test-docker-build
docker compose -f tests/docker-compose.yml run --rm test
```

### Roadmap

- [x] Add support for base URLs and relative URLs: You can specify the base URL as environment variable; it is then combined with the specific test's URL if the specific's test URL is a relative URL. This allows users to use the same autotester.yml in different environments (e.g. test, prod) which share the same relative URLs but different base URLs

## Credits

- [Powered by BrowserUse](https://github.com/browser-use/browser-use)
- This project evolved from an earlier open-source project developed by Tailor Media Inc, relased under Apache 2.0 [Codebeaver](https://github.com/codebeaver-ai/codebeaver-ai)
