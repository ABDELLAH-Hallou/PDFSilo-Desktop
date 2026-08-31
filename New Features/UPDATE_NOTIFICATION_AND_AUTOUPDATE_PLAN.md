# PDFSilo: Update Notification & One-Click Auto-Update Plan

_Drafted: 27 July 2026_

## Implementation status

_Updated: 30 August 2026_

The safe notification and verified-download boundary is implemented:

- [x] ADR 0006 records the first optional network capability.
- [x] `pdfsilo.updater` provides structured models, typed errors, semantic
      version comparison, fixed-host GitHub metadata checks, platform-asset
      selection, download progress, and SHA-256 verification without Qt.
- [x] Automatic checks are opt-in, off by default, and throttled to once per
      24 hours.
- [x] Settings allowlist the automatic-check flag, last-check timestamp, and
      skipped version; Restore defaults removes optional history.
- [x] **Help → Check for Updates…** supports explicit manual checks.
- [x] A Qt thread-pool adapter keeps checks and downloads off the GUI thread.
- [x] A non-blocking banner provides Update, Release notes, Skip this version,
      and dismiss actions.
- [x] The update dialog downloads to a per-user cache, verifies SHA-256, and
      can open the containing folder.
- [x] `pdfsilo update --check` exposes headless CLI parity.
- [x] Network-free tests cover the updater, opt-in boundary, settings, workers,
      banner/dialog, checksum deletion, and CLI.
- [x] Phase 13 now defines the standalone Windows artifact, per-user Inno
      installer layout, SHA-256 sidecars, and a separate Authenticode
      sign/verify release step in ADR 0007.
- [x] Phase 14 provides a tag-only Windows release workflow that publishes
      SHA-256 plus signing-status metadata. ADR 0009 permits exact version
      `v0.1.0` to publish unsigned with explicit warnings; all later versions
      fail closed without signing credentials.
- [x] ADR 0010 separates the private development repository from the public,
      README-only release channel. The updater reads only that fixed public
      repository's latest-release endpoint.
- [ ] Signature verification awaits signed Phase 13 artifacts.
- [ ] Platform **Install and restart** remains disabled until signature
      verification and installer arguments are defined per platform.
- [ ] Fully unattended Stage B updates remain future work.

The implementation deliberately does not execute downloaded code. This is
especially important for unsigned `v0.1.0`: a checksum proves integrity, not
publisher authenticity. Enabling installation before code-signature
verification would violate the security requirements below.

## 0. Why this needs care before it needs code

PDFSilo's entire product identity is **local-only PDF processing** and a
**strict settings allowlist** (ADR 0004). Before this feature, nothing made a
network call. Update checking is the first legitimate reason for PDFSilo to
talk to the internet at all, which makes it a privacy decision before it is an
engineering task.

Two consequences follow directly from the existing architecture:

- This should be recorded as a new ADR (**ADR 0006**), not just shipped
  silently, per the append-only ADR convention in `docs/adr/README.md`.
- Per the guiding principle in the migration plan ("PySide6 should be a
  client of the PDFSilo processing engine, not part of the processing
  engine"), the **update-check and download logic must not live in Qt code**.
  It belongs in a new framework-independent package, with Qt only adapting it
  to signals/UI — exactly how `pdfsilo.operations` is adapted by
  `pdfsilo.ui.workers` today.

Recommended default posture: **update checking is opt-in, off by default (or
prompted once on first run), never silent, and never uploads anything about
the user's documents.** The only network traffic is "is there a newer
version" and, if the user clicks Update, downloading the new release
artifact.

---

## 1. New ADR to write first

Create `docs/adr/0006-opt-in-update-checks-and-user-initiated-install.md`
before writing code, covering:

- **Decision**: PDFSilo may check a public release feed for a newer version.
  Checking is disabled by default / opt-in via Settings. No document content,
  file paths, or telemetry are ever transmitted. The only outbound request is
  a GET to a fixed, versioned release-metadata URL over HTTPS.
- **Consequences**: adds one new allowlisted settings group; adds a new
  non-Qt package `pdfsilo.updater`; requires code-signing/checksum
  verification before any downloaded binary is executed; requires a new
  "Update available" surface in the UI.

This keeps the decision reviewable and consistent with how ADR 0003–0005
were handled.

---

## 2. Where this lives in the architecture

```text
pdfsilo.updater            <- NEW, no Qt import, mirrors pdfsilo.core style
    check_for_update()     -> UpdateInfo | None
    download_update(...)   -> Path (staged installer/asset)
    verify_update(...)     -> bool (checksum + signature)
    apply_update(...)      -> FUTURE: signed platform install + relaunch

pdfsilo.ui.workers         <- extend with UpdateCheckWorker / UpdateWorker
                               (QThreadPool, same pattern as OperationWorker)

pdfsilo.ui.widgets         <- NEW: UpdateBanner / UpdateDialog

pdfsilo.ui.preferences     <- extend allowlist with updates/* keys
```

This mirrors ADR 0001 exactly: `pdfsilo.updater` gets a structured result
type and typed errors, and the CLI *and* GUI can both use it (a
`pdfsilo update` / `pdfsilo update --check` CLI command is a natural free
extra once the core exists — see step 10).

---

## 3. Data model

```python
# pdfsilo/updater/models.py
from dataclasses import dataclass

@dataclass(frozen=True)
class UpdateInfo:
    version: str                 # e.g. "0.2.0"
    download_url: str            # platform-specific asset URL
    checksum_sha256: str
    signature_url: str | None    # detached signature, if signing is set up
    release_notes_url: str
    published_at: str
    mandatory: bool = False      # allow future forced-security-update flag
    asset_name: str = ""
    checksum_url: str | None = None


class UpdaterError(Exception):
    """Base class for expected updater errors."""

class UpdateCheckFailedError(UpdaterError): ...
class UpdateDownloadError(UpdaterError): ...
class UpdateVerificationError(UpdaterError): ...
class UpdateApplyError(UpdaterError): ...
```

This follows the same `PdfSiloError`-subclass pattern already established, so
the CLI and GUI can each translate these errors idiomatically instead of
catching broad exceptions.

---

## 4. Choosing the release feed

Simplest option that needs zero new infrastructure: **GitHub Releases**,
since the About dialog already links to a homepage/issue tracker.

- Publish each release as a GitHub Release tagged `vX.Y.Z`, with one asset
  per platform (`PDFSilo-Setup-X.Y.Z.exe`, `PDFSilo-X.Y.Z.dmg`,
  `PDFSilo-X.Y.Z.AppImage`), each with a companion `.sha256` file.
- `check_for_update()` does one GET to
  `https://api.github.com/repos/<org>/pdfsilo/releases/latest`, compares the
  tag against the running app's version (from `pdfsilo.__version__`, already
  defined via `pyproject.toml`), and returns `UpdateInfo` or `None`.
- When GitHub supplies the asset's `sha256:` digest in release metadata, that
  value is used directly. Otherwise the companion `.sha256` asset is fetched
  only after the user chooses to download.
- No custom update server to build, host, or secure for v1. A self-hosted
  JSON feed can replace this later without changing anything above the
  `pdfsilo.updater` boundary.

Network access note: `pyside6-deploy`/Nuitka builds are static local binaries
today with no outbound calls — this is a genuinely new capability, which is
exactly why it needs the ADR and an explicit opt-in toggle, not just a
try/except around a `requests.get`.

---

## 5. Settings additions (extends ADR 0004's allowlist)

Add exactly these keys, nothing else, to the existing allowlist in
`pdfsilo.ui.preferences`:

| Key | Type | Default | Purpose |
|---|---|---|---|
| `updates/check_automatically` | bool | `false` (or prompt once, see §6) | master opt-in switch |
| `updates/last_check_timestamp` | str (ISO 8601) | unset | throttles checks to ~once/day |
| `updates/skipped_version` | str | unset | lets the user dismiss one version without being renagged until the next release |

No download history, no installed-version history beyond the current
running version, no machine identifiers. This keeps the feature inside the
spirit of ADR 0004's "no generic persistence" rule — three new keys, each
justified individually, same as the existing six.

The Settings dialog's **Restore defaults** button must reset these three keys
too.

---

## 6. First-run / opt-in UX

On first launch after this feature ships (detect via a one-time settings
migration flag, not a new persisted "have I asked" key that lingers forever —
reuse the existing Settings-dialog "Startup" tab instead):

- Add a checkbox to the Startup/privacy tab: **"Automatically check for
  PDFSilo updates"** — off by default.
- Add explanatory text directly under it: *"PDFSilo will contact GitHub to
  check the latest version number. No document data is ever sent."*
- If left off, the user can still check manually any time via
  **Help → Check for Updates…**, which is always available regardless of the
  toggle (a manual, explicit user action doesn't need the same default
  posture as background polling).

---

## 7. Background check flow (when enabled)

1. On app startup, if `updates/check_automatically` is true **and**
   `last_check_timestamp` is more than 24h old (or unset), enqueue an
   `UpdateCheckWorker` on the existing `QThreadPool` — same mechanism as
   `OperationWorker` (ADR 0002), so this reuses tested infrastructure rather
   than inventing a second concurrency model.
2. The worker calls `pdfsilo.updater.check_for_update()` off the GUI thread.
3. On success, if `UpdateInfo.version` is newer than the running version and
   is not equal to `updates/skipped_version`, emit a Qt signal back to the
   main thread.
4. `MainWindow` shows a **non-blocking banner** at the top of the window
   (not a modal dialog — never interrupt a user mid-operation), with:
   - "PDFSilo 0.2.0 is available (you have 0.1.0)."
   - **Update** button
   - **Release notes** link (opens `release_notes_url` in the default
     browser via `QDesktopServices`)
   - **Skip this version** / dismiss (✕)
5. On failure (offline, GitHub unreachable, rate-limited), fail silently —
   log it internally, do not surface an error dialog for a background check
   the user didn't explicitly request. Update `last_check_timestamp` anyway
   so it doesn't retry every launch while offline.
6. Manual **Help → Check for Updates…** runs the same worker but *does* show
   a small dialog on every outcome, including "You're up to date" and
   explicit failure ("Couldn't reach GitHub: <reason>"), since this path was
   user-initiated.

---

## 8. What "click Update and it just works" actually requires

This is the part that needs the most honesty: **fully silent, automatic
in-place updating is a different (and much larger) engineering commitment
than "check and notify," and it interacts directly with Phase 13/14 (native
packaging, code signing, CI) which are still open in the migration plan.**
It should be built in two clearly separated stages.

### Stage A — Assisted update (build this first, ship it)

Clicking **Update** in the banner/dialog:

1. Opens an `UpdateDialog` reusing the existing `ProgressDisplay` widget
   pattern from `OperationPanel` (§ ARCHITECTURE.md "desktop execution
   flow") — same look and feel as any long-running operation.
2. `UpdateWorker.download_update(info)` downloads the platform asset to a
   temp path (e.g. `%LOCALAPPDATA%\PDFSilo\updates\` /
   `~/Library/Caches/PDFSilo/updates/` / `~/.cache/pdfsilo/updates/`),
   reporting progress via the same `ProgressCallback` protocol from
   `pdfsilo.core.progress` — no new progress mechanism needed.
3. `verify_update()` checks the SHA-256 checksum against the published
   `.sha256` file. If code signing is set up (see §9), also verify the
   detached signature. **Any failure here hard-stops with
   `UpdateVerificationError` and deletes the downloaded file** — never launch
   an unverified binary.
4. On success, the dialog shows **"Downloaded and verified. Install and
   restart now?"** with **Install & Restart** / **Later** buttons — one
   click, but still a confirmed final step, exactly like the existing "Save
   result" review boundary in ADR 0003.
5. Clicking **Install & Restart** launches the platform installer/updater in
   detached mode and calls `QApplication.quit()`:
   - **Windows**: launch the downloaded `.exe`/MSIX silently
     (`/S` or `/quiet` depending on the installer tool chosen in Phase 13)
     via `subprocess.Popen(..., close_fds=True)`, detached from the current
     process, then quit PDFSilo so the installer can replace files that are
     currently in use.
   - **macOS**: mount the `.dmg`, or if using a self-updating `.app`, replace
     the bundle in `/Applications` via a small helper script (macOS won't let
     a running app overwrite its own bundle cleanly) launched detached, then
     quit.
   - **Linux (AppImage)**: since AppImages are single immutable files, "in
     place" means downloading the new AppImage next to the old one,
     `chmod +x`, and either (a) if launched via a known, writable path,
     replace it and relaunch, or (b) simply open the containing folder and
     tell the user to swap files — Linux packaging strategy should be
     finalized in Phase 13 before over-engineering this path.
6. On next launch, the new version's About dialog is the confirmation of
   success — no separate "did it work" telemetry is needed or wanted.

This stage gets you the actual UX the request describes — "the user clicks
Update and it happens automatically" — without silently executing arbitrary
downloaded code and without inventing a new background-service architecture.

### Stage B — Fully unattended background updates (explicitly future work)

Only pursue this after Stage A has shipped and Phase 13/14 packaging and
signing are solid. It requires:

- A signed differential/full updater package (e.g. Squirrel, Sparkle for
  macOS, or a custom signed updater), which is a meaningfully larger
  surface area than what PySide6/Nuitka gives you out of the box.
- Elevated-permission install handling on Windows if installed per-machine
  rather than per-user.
- A decision on whether unattended updates are ever appropriate for a
  privacy/security tool at all — many users of a local-only PDF tool will
  specifically want to control exactly when the binary on their machine
  changes. This is worth a product conversation, not just an engineering
  one.

**Recommendation: ship Stage A only for the initial release of this
feature.**

---

## 9. Security requirements (non-negotiable regardless of stage)

- All requests over HTTPS only; pin to the known GitHub API host.
- Verify SHA-256 checksum of every downloaded asset before touching it.
- Once Phase 13 code signing exists, verify the code signature of the
  downloaded installer/binary as well, before execution — checksum alone
  only proves "not corrupted," not "actually from you."
- Never execute anything downloaded without both checks passing.
- Downloaded files go to a per-user cache directory, never silently into
  `PATH` or an auto-run location.
- No credentials, tokens, or user-identifying data are ever sent with the
  update-check request.

---

## 10. Optional CLI parity (small addition, consistent with ADR 0001)

Since `pdfsilo.updater` has no Qt dependency, exposing it in the CLI is
nearly free and keeps both interfaces at parity, matching the project's own
stated principle:

```bash
pdfsilo update --check     # prints current + latest version, exit code 0/1
pdfsilo update --install   # downloads, verifies, and launches the installer
```

This also gives you a headless way to test the update-check and
verification logic in CI without constructing a `QApplication`.

---

## 11. Testing plan (extends the existing `pytest-qt` suite)

| Area | What to cover |
|---|---|
| `pdfsilo.updater` (no Qt) | Version comparison logic; parsing a mocked GitHub API response; checksum verification pass/fail; signature verification pass/fail; network-error handling; never-hits-network-when-disabled |
| Settings | New `updates/*` keys are allowlisted and included in Restore defaults; toggle persists correctly |
| UI worker | `UpdateCheckWorker` runs off the GUI thread; signals delivered on GUI thread only, matching existing worker tests |
| Banner/dialog | Shown only when a newer version exists and isn't skipped; Skip persists `skipped_version`; dismiss doesn't reappear same session |
| Download/verify | Corrupted download is rejected and deleted; checksum mismatch raises `UpdateVerificationError` and never proceeds to install |
| Security regression | Assert no update-related network call occurs anywhere in the test suite when `check_automatically` is false (mirrors the existing "no sensitive settings persisted" regression tests) |
| CLI | `pdfsilo update --check` exit codes and output, matching existing CLI test conventions |

Use `responses` or `pytest-httpserver`-style mocking for the GitHub API so
the suite stays network-free, consistent with the current test boundaries in
`CODEBASE_ANALYSIS.md`.

---

## 12. Suggested implementation order

1. Write **ADR 0006** and get it accepted.
2. Build `pdfsilo.updater` core (check, download, verify) with no Qt import
   and full test coverage — this is directly reusable by the CLI.
3. Add the three `updates/*` settings keys and Settings-dialog checkbox.
4. Add `UpdateCheckWorker` + startup wiring (respecting the 24h throttle and
   opt-in flag).
5. Build the non-blocking banner and manual **Help → Check for Updates…**
   dialog.
6. Build the download/verify progress dialog reusing `ProgressDisplay`.
7. Implement Stage A platform-specific "install & restart" for **one**
   platform first (whichever ships first in Phase 13 — the plan already
   sequences Windows first), then extend to macOS/Linux once each has a
   real signed installer artifact from Phase 13.
8. Add the CLI `update` subcommand for parity and CI-friendly testing.
9. Only after all of the above is stable in production: evaluate Stage B.

---

## 13. Summary of what changes in existing docs

- `docs/adr/README.md` — add a row for ADR 0006.
- `docs/ARCHITECTURE.md` — add `pdfsilo.updater` to the package
  responsibilities table, and mention it in "Settings and privacy boundary."
- `PYSIDE6_MIGRATION_PLAN.md` — this feature fits naturally as new items
  under Phase 13/14, since it depends on real signed release artifacts.
