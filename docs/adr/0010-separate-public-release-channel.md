# ADR 0010: Separate Public Release Channel

- Status: Accepted
- Date: 2026-08-31

## Context

PDFSilo needs publicly downloadable desktop installers while its development
repository remains private. Publishing releases from the private repository
would make the download page unavailable to people without repository access.
Mirroring the application source, workflows, or build artifacts into a public
repository would unnecessarily expand the exposed attack surface.

## Decision

Use `ABDELLAH-Hallou/PDFSilo` as a public release-only repository. Its tracked
content is limited to a short user-facing README. GitHub Releases may contain
only finalized installers, portable archives, matching SHA-256 sidecars,
signing-status metadata, and the release manifest. Source, build scripts,
workflow logs, test artifacts, credentials, and internal documentation remain
in the private development repository.

Issues, Discussions, Wiki, Projects, and GitHub Actions are disabled in the
public repository. Immutable releases are enabled. Because a published release
cannot be changed, the private tag workflow creates a public draft, uploads the
complete verified asset set, checks that the remote names exactly match the
candidate, and only then publishes the draft. A published version is never
overwritten; a correction uses a new version.

Cross-repository publication uses the protected private `release` environment
secret `PDFSILO_RELEASE_REPOSITORY_TOKEN`. It must be a short-lived,
fine-grained credential restricted to the public repository with Contents
read/write permission. The token is supplied only to the publication step and
must never be copied into source, artifacts, release notes, or website
configuration.

Public release tags target the README-only `main` branch. GitHub's automatic
source archives therefore contain only that public README commit, not the
private application source.

## Consequences

- Anyone can download releases without access to the private source repository.
- The website and in-app updater use the public release repository as their
  single download/feed origin.
- Candidate builds remain private GitHub Actions artifacts and cannot be used
  as public download links.
- The public repository does not accept source contributions or support
  reports; product help is directed to `pdfsilo.com`.
- Public binaries can still be inspected or reverse engineered. Repository
  separation prevents accidental source and secret publication but cannot make
  distributed executable code opaque.
- Publishing requires the repository-scoped credential to be configured by an
  owner in the private repository's protected `release` environment.
