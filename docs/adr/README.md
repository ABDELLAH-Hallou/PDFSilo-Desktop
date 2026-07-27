# Architecture Decision Records

This directory records significant PDFSilo decisions. ADRs are append-only:
when a decision changes, add a superseding record instead of silently
rewriting the original rationale.

| ADR | Status | Decision |
|---|---|---|
| [0001](0001-shared-core-for-cli-and-gui.md) | Accepted | Share one structured core between CLI and GUI |
| [0002](0002-background-work-and-cooperative-cancellation.md) | Accepted | Run PDF and preview work outside the Qt UI thread |
| [0003](0003-staged-and-atomic-output-publication.md) | Accepted | Stage output and publish it safely |
| [0004](0004-allowlisted-non-sensitive-settings.md) | Accepted | Persist only allowlisted non-sensitive UI state |
| [0005](0005-theme-system-and-png-identity.md) | Accepted | Support system/light/charcoal-dark themes and use the supplied PNG identity |
| [0006](0006-opt-in-update-checks-and-user-initiated-install.md) | Accepted | Keep update checks opt-in and verify downloads before user-initiated installation |

The implementation overview lives in
[`docs/ARCHITECTURE.md`](../ARCHITECTURE.md).
