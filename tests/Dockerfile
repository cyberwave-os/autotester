FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

# Copy only what is required to install the package and run tests.
COPY pyproject.toml README.md /workspace/
COPY src /workspace/src
COPY tests /workspace/tests

RUN pip install --upgrade pip && pip install -e ".[test]"

CMD ["pytest"]
