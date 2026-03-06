# Contributing to Autotester

Thank you for your interest in contributing to Autotester! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Clone the repository:
2. Create a virtual environment and activate it:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install the package in development mode with test dependencies:
   ```bash
   pip install -e ".[test]"
   ```

## Running Tests

We use pytest for our test suite. To run the tests:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=autotester --cov-report=term-missing
```

### Running Tests with Docker

If you prefer not to manage local Python dependencies, use the Dockerized test runner:

```bash
make test-docker
```

This runs the same test suite inside a container using Python 3.11.
To build first and then run:

```bash
make test-docker-build
docker compose -f tests/docker-compose.yml run --rm test
```

## Code Style

We follow PEP 8 style guidelines. Before submitting a pull request, please ensure your code follows these standards.

You can check code style using:

```bash
# Install development dependencies
pip install black flake8

# Run black for code formatting
black .

# Run flake8 for style checking
flake8 .
```

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Update the documentation if needed.
5. Issue the pull request!

## License

By contributing to Autotester, you agree that your contributions will be licensed under its MIT license.
