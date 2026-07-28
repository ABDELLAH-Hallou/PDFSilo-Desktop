# ADR 0007: Standalone Windows Build and Per-User Installer

- Status: Accepted
- Date: 28 July 2026

## Context

PDFSilo needs a native Windows release that works without a system Python
installation. The first packaged form must remain inspectable and easy to
diagnose before optimizing distribution size. Public installation also
requires predictable application identity, an uninstall path, and a future
code-signing boundary.

Qt for Python supplies `pyside6-deploy`, which drives Nuitka and stores its
configuration in a reusable specification file. Nuitka supports both
directory-based standalone output and one-file output.

## Decision

1. Build the first Windows artifact with `pyside6-deploy` and Nuitka in
   `standalone` mode.
2. Keep the deployment configuration in the root `pysidedeploy.spec`.
3. Generate the Windows ICO deterministically from the supplied
   `pdfsilo/ui/resources/icon.png`; the incorrect legacy SVG identity is not
   used.
4. Embed the product name, file/product version, publisher, description, icon,
   and copyright in the executable.
5. Use an Inno Setup 6 definition for a per-user x64-compatible installer.
   Installation does not require elevation and defaults to
   `%LOCALAPPDATA%\Programs\PDFSilo`.
6. Produce SHA-256 sidecar files for transport-integrity metadata.
7. Keep signing separate from compilation. Release automation must sign and
   verify both the executable and installer with `signtool` before
   publication, then generate final checksums because signing changes bytes.
8. Do not enable updater execution or **Install and restart** until Windows
   Authenticode verification is implemented in the application.
9. Treat clean-machine testing and signing as release gates. Local smoke tests
   are useful evidence but cannot satisfy those external gates.

## Consequences

- The first artifact is larger than a one-file executable, but missing files
  and Qt plug-ins are directly inspectable.
- The directory must remain intact; copying only `PDFSilo.exe` is unsupported.
- A checked-in installer definition makes the install layout reviewable even
  on machines without Inno Setup.
- Developers need a supported compiler. A Visual Studio Developer PowerShell
  gives `pyside6-deploy` access to `dumpbin` for improved Qt dependency
  detection.
- Windows artifacts cannot be reused for macOS or Linux. Each platform must
  build and test its own native bundle.
- Publisher authenticity remains deliberately incomplete until a trusted
  certificate is available and signature verification is part of the release
  and updater paths.

## Validation status

The packaging inputs and Python-level contracts passed as part of the
382-test suite on 28 July 2026. A local Python 3.12/Nuitka 4.1.3 standalone
attempt completed analysis and most generated-object compilation, but MinGW
exhausted available memory on PyMuPDF's generated `module.pymupdf.mupdf.c`
with low-memory mode enabled, LTO disabled, and one compiler job. Therefore
this ADR records the selected release design, not a completed native release.
A successful higher-memory or MSVC build, frozen self-test, clean-VM run,
installer compilation, and signature verification remain acceptance gates.
