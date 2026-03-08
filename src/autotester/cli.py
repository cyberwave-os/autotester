"""
Command-line interface for Autotester
"""

import os

os.environ["ANONYMIZED_TELEMETRY"] = "false"
import sys
import argparse

import pathlib
import logging

from autotester.reporting import Report

from . import __version__
import yaml
from .E2E import E2E
import asyncio


def valid_file_path(path):
    """Validate if the given path exists and is a file."""
    file_path = pathlib.Path(path)
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f"File not found: {path}")
    return str(file_path)


def setup_logging(verbose=False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(levelname)s: %(message)s"

    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format, stream=sys.stderr)

    # Create logger for our package
    logger = logging.getLogger("autotester")
    # Ensure the logger level is set correctly (in case it inherits a different level)
    logger.setLevel(log_level)

    # Test message to verify debug logging
    logger.debug("Debug logging is enabled")
    return logger


def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]

    # Create the main parser with more detailed description
    parser = argparse.ArgumentParser(
        description="""Autotester - AI-powered code analysis and testing

Autotester helps you run E2E tests for your code using AI.

Examples:
  autotester     # Run E2E tests if defined in autotester.yml
  autotester e2e    # Run end-to-end tests defined in autotester.yml
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"Autotester {__version__}"
    )

    # Add verbose flag
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging output"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # E2E test command with enhanced help
    e2e_parser = subparsers.add_parser(
        "e2e",
        help="Generate and run end-to-end tests",
        description="""Generate and run end-to-end tests based on a YAML configuration file.
        
The command will:
1. Read the E2E test configuration from the autotester.yml file
2. Set up the test environment
3. Execute the end-to-end tests
4. Report the results

Examples:
  autotester e2e --config=autotester.yml
""",
    )
    e2e_parser.add_argument(
        "--config",
        default="autotester.yml",
        help="Path to the YAML configuration file (defaults to autotester.yml)",
        dest="yaml_file",  # Keep the same variable name for compatibility
    )
    # Add verbose flag to e2e parser
    e2e_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging output"
    )

    args = parser.parse_args(args)

    # Setup logging before any other operations
    logger = setup_logging(args.verbose)

    # Check environment variable after parsing arguments
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY environment variable is not set")
        sys.exit(1)

    # If no command specified, run E2E tests if defined in config
    if not args.command:
        try:
            with open("autotester.yml", "r") as f:
                config = yaml.safe_load(f)

            if "e2e" in config:
                logger.info("Running e2e tests...")
                args.command = "e2e"
                args.yaml_file = "autotester.yml"  # Set the yaml_file attribute

                run_e2e_command(args)
            else:
                logger.info("No E2E Tests configured in autotester.yml, skipping...")

            if "e2e" not in config:
                logger.error(
                    "No tests configured in autotester.yml. Check out the documentation at https://github.com/autotester-ai/autotester-ai for more information."
                )
                sys.exit(1)

        except FileNotFoundError:
            logger.error("Could not find autotester.yml")
            sys.exit(1)
    else:
        # Handle specific commands as before
        if args.command == "e2e":
            run_e2e_command(args)
        else:
            logger.error("Error: Please specify a valid command (e2e)")
            sys.exit(1)


def run_e2e_command(args):
    """Run the e2e test command."""
    logger = logging.getLogger("autotester")
    logger.debug(f"E2E testing with YAML file: {args.yaml_file}")

    try:
        valid_file_path(args.yaml_file)
        with open(args.yaml_file, "r") as f:
            yaml_content = yaml.safe_load(f)
            if "e2e" not in yaml_content:
                logger.error("Error: No e2e tests found in the YAML file")
                sys.exit(1)

            e2e_section = dict(yaml_content["e2e"])
            auth = e2e_section.pop("auth", None)
            if auth and auth.get("type") and auth["type"] != "basic":
                logger.error(
                    f"Unsupported auth type '{auth['type']}'. Only 'basic' is currently supported."
                )
                sys.exit(1)

            e2e = E2E(
                e2e_section,
                chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                auth=auth,
            )
            e2e_tests = asyncio.run(e2e.run())
            report = Report(e2e_tests)
            report.to_console()
    except Exception as e:
        logger.error(f"Error reading YAML file: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
