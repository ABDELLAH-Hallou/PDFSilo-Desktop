# ADR 0009: Unsigned v0.1.0 Bootstrap Release

- Status: Accepted
- Date: 30 August 2026
- Supersedes: the no-unsigned-publication rule in ADR 0008 for `v0.1.0` only

## Context

PDFSilo's Windows packaging, checksum generation, frozen application tests,
and clean install/uninstall workflow are ready, but the project does not yet
have a publicly trusted Authenticode signing identity. Obtaining and
integrating an HSM- or cloud-backed certificate requires external identity,
billing, and provider approval work.

The project owner has chosen to publish the first Windows release before that
work finishes. Windows can run unsigned applications, but it identifies the
publisher as unknown and Microsoft Defender SmartScreen can present an
additional warning. A SHA-256 checksum can detect changed bytes; it cannot
authenticate the publisher.

## Decision

1. Permit an unsigned public Windows release only for the exact stable tag
   `v0.1.0`.
2. Keep the exception hard-coded in the release workflow. Do not add a general
   workflow input, repository variable, or manual override that can enable
   unsigned publication for another version.
3. Continue to require version agreement, the complete test suite, the frozen
   application tests, SHA-256 verification, and a fresh-runner
   install/test/uninstall cycle before publication.
4. Require the standalone executable and installer to report `NotSigned` when
   the exception is used. Record `scheme: none`, `mode: unsigned-exception`,
   artifact status, and an explicit warning in `windows-signing.json` and the
   aggregate release manifest.
5. Put a prominent unknown-publisher and SmartScreen warning in the GitHub
   Release notes. Publish `.sha256` sidecars with the installer and standalone
   ZIP.
6. Keep automatic installer execution disabled. Update checks and verified
   downloads may continue, but PDFSilo only opens the containing folder for a
   user-initiated installation.
7. If valid signing credentials are configured, sign `v0.1.0` normally rather
   than using the exception.
8. Every tag other than `v0.1.0` must fail closed unless both Windows signing
   credentials are configured. Signed releases must have valid Authenticode
   signatures and RFC 3161 timestamps on the main executable and installer.

## Consequences

- Users of `v0.1.0` must consciously accept Windows's unknown-publisher or
  SmartScreen warning.
- The first release has integrity metadata but no cryptographic proof of the
  publisher's identity.
- Distribution pages must describe `v0.1.0` as unsigned and must not use terms
  such as "verified publisher" or imply that SHA-256 is a signature.
- The exception cannot silently carry into `v0.1.1`, `v0.2.0`, or any other
  release.
- ADR 0008 remains in force for ordinary CI, tag-gated publication,
  least-privilege permissions, signed releases, and all later versions.
