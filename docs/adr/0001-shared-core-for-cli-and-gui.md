# ADR 0001: Share one structured core between CLI and GUI

- Status: Accepted
- Date: 24 July 2026

## Context

The original operations accepted strings, logged their own failures, caught
broad exceptions, and returned booleans. Those conventions were sufficient for
a CLI but could not give a desktop interface structured success details or
specific expected failures.

## Decision

Every operation exposes `execute(...) -> OperationResult`, accepts
`pathlib.Path` values, and raises typed `PdfSiloError` exceptions for expected
failures. The operation layer contains no Qt imports and makes no
presentation-specific logging decisions.

The CLI and PySide6 application are adapters over that contract. Compatibility
`run(...) -> bool` functions remain available through the presentation
adapter.

## Consequences

- PDF behavior has one implementation for both interfaces.
- Core tests do not require a Qt application.
- The CLI can retain its established behavior while the GUI displays richer
  results and errors.
- New operations must define their structured result and expected failure
  behavior before adding presentation code.
