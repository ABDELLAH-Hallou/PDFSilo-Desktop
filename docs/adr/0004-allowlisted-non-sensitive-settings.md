# ADR 0004: Persist only allowlisted non-sensitive UI state

- Status: Accepted
- Date: 27 July 2026

## Context

Useful desktop preferences improve repeated workflows, but recent files,
document paths, and passwords would conflict with PDFSilo's privacy-first
position and create unnecessary secret-retention risk.

## Decision

`QSettings` uses an explicit allowlist for:

- Theme mode
- Preview visibility
- Overwrite confirmation
- Opening the output folder after saving
- Restoring window geometry/state
- Reopening the last tool
- The optional geometry, state, and navigation values those choices enable

No form field is persisted generically. Document paths, contents, recent-file
history, and passwords are excluded. Disabling restoration removes the related
stored window or navigation values. The Settings dialog provides **Restore
defaults**.

## Consequences

- Users retain practical appearance, workflow, and startup preferences.
- The persistence boundary is reviewable and covered by security tests.
- New settings require an explicit schema change and privacy review.
- PDFSilo cannot offer recent-document reopening without a future decision
  that revisits this privacy tradeoff.

## Later extension

[ADR 0006](0006-opt-in-update-checks-and-user-initiated-install.md) extends
this allowlist with three narrowly scoped update keys: automatic-check opt-in,
last-check timestamp, and skipped version. It preserves the original
no-generic-persistence rule and still excludes documents, paths, credentials,
and telemetry.
