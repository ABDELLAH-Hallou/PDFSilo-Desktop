# Windows Packaging

PDFSilo uses Qt for Python's `pyside6-deploy` wrapper around Nuitka. The
checked-in `pysidedeploy.spec` deliberately uses `standalone` mode so the first
release is an inspectable directory build.

## Prerequisites

- Windows 10 or 11, x64
- A CPython 3.12 or 3.13 virtual environment with PDFSilo development and
  deployment dependencies. Python 3.14 is supported by PDFSilo itself, but
  remains experimental in the pinned Nuitka version.
- Nuitka's supported Zig compiler backend for Windows x64. The checked-in
  deployment specification selects `--zig` because MSVC exhausts its compiler
  heap on PyMuPDF's generated wrapper on the standard GitHub-hosted runner.
- Inno Setup 6 for installer creation
- Windows SDK `signtool.exe` and a trusted code-signing certificate for public
  releases

Qt recommends running deployment inside a virtual environment. On Windows,
MSVC's `dumpbin` improves Qt dependency detection; run the build from a
Developer PowerShell when available.

## Build and test

```powershell
python -m pip install -e ".[dev,deploy]"
.\scripts\build_windows.ps1
.\scripts\test_windows_package.ps1
```

The script uses `venv\Scripts\python.exe` by default. A dedicated packaging
environment can be selected explicitly:

```powershell
.\scripts\build_windows.ps1 `
  -PythonPath ".\venv-deploy\Scripts\python.exe"
```

The second command launches the frozen GUI briefly, then runs representative
rotate, compression, encryption, and decryption workflows from the frozen
executable using Unicode and deeply nested paths. Results are written to:

```text
dist/windows/package-validation/pdfsilo-package-self-test.json
```

### Build troubleshooting

PyMuPDF contains a very large generated wrapper. C compilers can exhaust memory
while compiling it: the 28 July 2026 local MinGW attempt failed
on `module.pymupdf.mupdf.c` after the single compiler process reached about
2.8 GiB, despite Nuitka low-memory mode and disabled LTO. Use a higher-memory
Windows builder or install MSVC Build Tools and build from a Developer
PowerShell. Python 3.12 or 3.13 is recommended over the experimental Python
3.14 deployment path. Do not publish an artifact from a build that ended with
a Nuitka crash report.

On 29 August 2026, the pinned deployment stack completed locally with Python
3.14 and Zig after a long, paging-heavy compile. The resulting executable
passed the 120-page frozen self-test, and Inno Setup 6.7.3 produced an installer
that passed a silent install/test/uninstall cycle. The first remote Python 3.12
candidate then proved that MSVC also fails on the wrapper with `C1002`. Python
3.12 with Nuitka's Zig backend is now the release-workflow baseline.

## Installer

After installing Inno Setup:

```powershell
.\scripts\build_windows_installer.ps1 -Version 0.1.0
```

The per-user installer is written to `dist/installer` with a companion
`.sha256` file.

## Signing

Sign both the standalone executable and final installer with a trusted
certificate:

```powershell
.\scripts\sign_windows_artifacts.ps1 `
  -CertificateThumbprint "YOUR_CERTIFICATE_THUMBPRINT" `
  -ArtifactPath @(
    ".\dist\windows\PDFSilo.dist\PDFSilo.exe",
    ".\dist\installer\PDFSilo-Setup-0.1.0-x64.exe"
  )
```

Normally, never publish an installer until `signtool verify /pa /all`
succeeds. Generate the final checksum after signing because signing changes
the file bytes. ADR 0009 permits one explicit exception: `v0.1.0` may be
published unsigned with unknown-publisher warnings, signing-status metadata,
SHA-256 sidecars, and all other release gates. No later version may use that
exception.

## Clean-machine release gate

Copy the installer to a Windows VM without Python or developer tools and verify:

1. Install and uninstall complete successfully.
2. Start menu and optional desktop shortcuts work.
3. `PDFSilo.exe --smoke-test` exits with code zero.
4. Normal GUI startup displays the PNG identity and both themes.
5. Merge, split, compression, encryption, and decryption work.
6. Unicode, deeply nested, large, invalid, and encrypted inputs behave safely.
7. The installed executable and installer signatures validate.
