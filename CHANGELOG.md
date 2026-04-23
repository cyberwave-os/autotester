## [0.1.2] - 2026-04-22

### Fixed

- Basic-auth URLs (`https://user:pass@host/path`) were being mangled by
  browser-use's task-text URL extractor, which strips anything matching
  an "email" regex. The `pass@host` substring looked like an email and
  was deleted, leaving a broken `https://user:/path` that failed DNS
  resolution. The credentialed URL is now passed to the Agent via
  `initial_actions` (which bypasses URL extraction), while only the
  clean URL remains in the LLM-visible task text.

## [0.0.8] - 2026-03-08

### Added

- Support for Posthog session recording
- Support for base URL configuration
- Support for HTTP Basic Auth configuration
- Added the example folders

## [0.0.1] - 2026-03-08

### Added

- Initial project setup

### Notes

This is the first beta release of Autotester. While the core functionality is stable,
some features are still under development. We welcome feedback and contributions from the community.
