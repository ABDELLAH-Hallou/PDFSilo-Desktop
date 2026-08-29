# ADR 0008: CI Matrix and Tag-Gated Signed Releases

- Status: Accepted
- Date: 28 July 2026

## Context

PDFSilo needs repeatable checks for its Qt-free processing layer, desktop
interface, package metadata, and native application packaging. Pull requests
must not receive release permissions or signing material. A release must also
be traceable to a versioned Git tag and must not publish an unsigned Windows
installer.

Windows x64 is currently the only supported native release target. Linux and
macOS are test targets, but their native package formats and signing processes
have not yet passed Phase 13 acceptance.

## Decision

1. Run `.github/workflows/ci.yml` on branch pushes, pull requests, and manual
   requests with read-only repository permission.
2. Install PDFSilo from `pyproject.toml` in every job.
3. Run Qt-free core and CLI tests on Python 3.10 through 3.14 on Ubuntu.
4. Run headless-compatible UI tests on Ubuntu, Windows, and Intel macOS with
   `QT_QPA_PLATFORM=offscreen`.
5. Use pinned Ruff 0.15.22 for both static analysis and formatting checks.
6. Build the wheel and source distribution and retain them as workflow
   artifacts.
7. Allow `.github/workflows/release.yml` to run manually for a signed,
   non-publishing release candidate or from tags matching `v*.*.*`. In both
   cases, strictly validate the stable `vMAJOR.MINOR.PATCH` form and require
   the requested version to match `pyproject.toml`, `pdfsilo.__version__`, and
   Windows executable metadata.
8. Give `contents: write` only to the tag-gated publication job.
9. Require the protected `release` environment to provide
   `WINDOWS_SIGNING_CERTIFICATE_BASE64` and
   `WINDOWS_SIGNING_CERTIFICATE_PASSWORD`. Missing secrets fail the release;
   there is no unsigned fallback.
10. Build and test the standalone Windows directory, Authenticode-sign its
    executable, build and sign the Inno Setup installer, and verify both
    signatures before publication.
11. Download the signed installer onto a fresh Windows runner, reverify its
    checksum and Authenticode signature, install it, run the packaged workflow
    test from the installed application, and uninstall it.
12. Preserve the signed standalone directory and release assets as Actions
    artifacts. Publish the installer, standalone ZIP, SHA-256 companions,
    Authenticode metadata, and an aggregate release manifest through GitHub's
    authenticated CLI.

## Consequences

- Ordinary CI and pull requests cannot publish releases or read signing
  secrets.
- Maintainers can exercise the complete signed packaging and clean-install
  path without creating a public GitHub Release.
- A version tag with inconsistent metadata fails before native compilation.
- Release publication depends on a trusted code-signing certificate, timestamp
  service, Visual C++ Build Tools, Inno Setup, and enough memory for Nuitka.
- A local standalone build, frozen self-test, installer build, per-user
  install, and uninstall succeeded on 29 August 2026. The first signed remote
  candidate still needs to prove the complete GitHub-hosted path.
- Linux and macOS remain headless test targets. Add their release jobs only
  after platform-specific package, signing, and clean-machine validation exist.
- SHA-256 proves byte integrity, while the recorded and verified Authenticode
  signature establishes Windows publisher authenticity.
