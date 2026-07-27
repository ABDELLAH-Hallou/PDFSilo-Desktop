# ADR 0006: Opt-in update checks and user-initiated installation

- Status: Accepted
- Date: 27 July 2026

## Context

PDFSilo processes documents locally and previously made no network requests.
Checking for releases is the first legitimate network capability and therefore
changes the product's privacy boundary. Native packaging, installer signing,
and per-platform replacement behavior are not yet complete.

## Decision

PDFSilo may make an HTTPS GET request to its fixed public GitHub Releases
endpoint to check for a newer version. Automatic checks are disabled by
default and must be enabled explicitly in Settings. A manual **Help → Check
for Updates…** action remains available.

Update traffic contains no document data, file paths, credentials, telemetry,
or machine identifier. The settings allowlist gains only:

- `updates/check_automatically`
- `updates/last_check_timestamp`
- `updates/skipped_version`

Release checking, version comparison, download, and SHA-256 verification live
in the framework-independent `pdfsilo.updater` package. Qt only adapts that
contract to background workers and UI.

Downloaded assets are staged in a per-user cache and must pass their published
SHA-256 checksum. PDFSilo does not execute a downloaded asset until Phase 13
defines a signed installer for the platform and the application can verify its
code signature. The current interface may download and verify an artifact,
then show it in its containing folder; installation remains user-initiated.

## Consequences

- No update-related network call occurs while automatic checking is disabled,
  unless the user explicitly invokes the manual action.
- Background checks are throttled to once per 24 hours and fail without
  interrupting document work.
- Manual checks report up-to-date, available, and failure outcomes.
- A non-blocking banner can announce a newer, non-skipped version.
- New updater logic remains usable by both CLI and GUI and testable without
  constructing Qt.
- Fully automatic install/restart remains blocked on signed native release
  artifacts and platform-specific installer contracts.
