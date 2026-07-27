# ADR 0003: Stage output and publish it safely

- Status: Accepted
- Date: 25 July 2026

## Context

Writing directly to a destination can leave a partial file after failure or
cancellation and can replace an existing document before the user reviews the
result.

## Decision

Core single-file operations use temporary output and atomic replacement where
practical. Folder-producing operations use staging directories and remove
temporary work after cancellation.

PDF-producing desktop workflows keep successful output staged for visual
review. The destination changes only after **Save result**. **Discard result**
deletes the staged output. Replacing an existing destination requires
confirmation by default.

## Consequences

- Existing documents survive most processing failures and cancellations.
- Users can inspect generated PDFs before publication.
- Temporary output has an explicit owner and cleanup lifecycle.
- Complete transactional rollback for every multi-file failure remains future
  work.
