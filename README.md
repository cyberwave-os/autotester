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

That's it. To run it, you need to have an OpenAI API key and Chrome installed.

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

Autotester can be used in a [GitHub Action](https://github.com/cyberwaveos/autotester-oss-action) to run E2E tests after you release a new version.

Check out the action's [README](https://github.com/cyberwaveos/autotester-oss-action/blob/main/README.md) for more information, but here's a quick example:

```yaml
name: Run Autotester

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  after-deployment:
    runs-on: ubuntu-latest
    steps:
      - uses: cyberwaveos/autotester-oss-action@v0.1.0
        with:
          action-type: "e2e"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          STARTING_URL: "http://yourstaging.yourwebsite.com"
```

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

### Supported Languages and Frameworks

Autotester currently supports:

- Python
- TypeScript

## Credits

- [Powered by BrowserUse](https://github.com/browser-use/browser-use)
- This project evolved from an earlier open-source project developed by Tailor Media Inc, relased under Apache 2.0 [Codebeaver](https://github.com/codebeaver-ai/codebeaver-ai)
