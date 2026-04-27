## [0.1.4] - 2026-04-27

### Added

- Local MP4 video recording for every E2E test run, powered by browser-use's
  built-in CDP screencast recorder. Each test now writes
  `.autotester/videos/<test-name>/<test-name>.mp4` and the path is exposed on
  the `End2endTest` result (and serialized into `e2e.json` / `e2e.xml`).
- The `browser-use[video]` extra is now a hard dependency, pulling in
  `imageio[ffmpeg]` so the recorder works out of the box (no manual
  install). Failed tests still get an optional Posthog session-replay link
  on top of the local MP4.

### Changed

- `E2E.run_test` now returns a 3-tuple `(TestCase, recording_url,
  video_path)` instead of `(TestCase, recording_url)`. Callers that
  destructure the result must be updated.

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
