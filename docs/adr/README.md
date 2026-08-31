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
| [0007](0007-standalone-windows-build-and-per-user-installer.md) | Accepted | Ship an inspectable standalone Windows build before one-file packaging |
| [0008](0008-ci-matrix-and-tag-gated-signed-releases.md) | Accepted; amended by 0009 | Test across supported runtimes and require signed, tag-gated native releases |
| [0009](0009-unsigned-v0-1-0-bootstrap-release.md) | Accepted | Permit one clearly disclosed unsigned bootstrap release for v0.1.0 only |
| [0010](0010-separate-public-release-channel.md) | Accepted | Publish verified downloads through a separate README-only public repository |

The implementation overview lives in
[`docs/ARCHITECTURE.md`](../ARCHITECTURE.md).
