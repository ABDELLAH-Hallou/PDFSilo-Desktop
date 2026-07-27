# ADR 0005: Use system/light/charcoal-dark themes and PNG identity assets

- Status: Accepted
- Date: 27 July 2026

## Context

The desktop UI needs a consistent, accessible visual system and must respect
users who prefer light, dark, or operating-system-controlled appearance. An
early dark palette used large blue/navy surfaces and early SVG identity files
did not match the approved product artwork.

The supplied `logo.png` and `icon.png` are the authoritative designs.

## Decision

PDFSilo supports System default, Light, and Dark modes:

- System default follows Qt's current OS color scheme.
- Light mode uses neutral document surfaces, indigo primary actions, and teal
  accents.
- Dark mode uses neutral charcoal canvas, sidebar, card, and alternate
  surfaces. Indigo and teal are accents rather than page backgrounds.

The application loads `logo.png` for the sidebar wordmark and `icon.png` for
application, window, and About icons in every mode. Their empty transparent
promotional margins are cropped at runtime without recolouring or reshaping
the artwork. Dark mode may place the wordmark on a compact neutral light plate
to preserve contrast.

Theme SVG identity variants are not used at runtime. SVG remains appropriate
for functional control icons such as sidebar and spin-button arrows.

## Consequences

- The dark workspace reads as neutral dark rather than blue.
- One product identity is used consistently across themes and surfaces.
- PNG identity assets must remain in wheel package data.
- Tests protect system theme switching, charcoal palette roles, PNG resource
  loading, and the absence of runtime references to legacy identity SVGs.
