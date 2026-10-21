## [Unreleased]

### Added
- Standalone dimmers, LED groups, dimmer groups and output groups, adapted from PR #24 by @sebcie.
- Local Nexo weather observations without external forecast requests.
- Per-entry external command buttons, automatic discovery and a command-name options form.
- Regression tests for commands, entity IDs, callbacks, discovery and connection cleanup.

### Fixed
- Preserve existing light and switch entity IDs while adding new resource types.
- Stop background connection workers on successful unload and failed startup; retry when initial resources time out.
- Run synchronous and asynchronous resource callbacks without awaiting non-awaitable results.
- Stabilized Nexo WebSocket reconnect flow by removing rel-based dispatcher handling and running the connection loop in a dedicated thread.
- Added watchdog ping logic to keep the connection alive and trigger reconnect when the socket stops responding.
- Improved initialization and resource load handling to avoid stale or broken connection states during startup.
- Hardened WebSocket error handling and reconnect timing for more reliable operation in Home Assistant.

## [1.2.0] - 19.03.2024

### Added
- Websocket reconnection improvments
- Updated websocket-client version to 1.7.0
- Analog sensors temperature
- Blinds / Covers


## [1.1.0] - 26.11.2023

### Added
- Websocket reconnection
- Updated websocket-client version to 1.6.4
- Analog sensor integration
- Switch integration
- Fix for entities received after unsupported partition resource
- typos code quality ...

## [1.0.1] - 07.09.2023

### Added

- Binary Sensor integration


## [1.0.0] - 06.09.2023

### Added

- Lights integration.
