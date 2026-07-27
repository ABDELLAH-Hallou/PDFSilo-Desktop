# PDFSilo UI review findings

_Updated: 27 July 2026_

![The preview is not clear, it is low quality, can't zoom in/out, not including all the pdfs (only the first one when merging), it should give the right to order pdfs to merge, or images to include ..etc](image.png)
![instead of selecting all pdf in one shot, you should add a button thet will make me be able to add new pdf each time](image-1.png)
![when selecting a certain target page size it needs to be shown in the perview so I can see an example of how the output would be](image-2.png)
![two step process is better[ run process, view the results in preview and then click save]](image-3.png)
![the up and down buttons are not shown](image-4.png)

## Resolution

- [x] The PDF preview now renders at a higher resolution and provides zoom
      in, zoom out, and fit-to-window controls.
- [x] Merge previews include every selected PDF through an ordered document
      selector, with page navigation inside the selected document.
- [x] PDF and image inputs can be added incrementally, reordered with
      drag-and-drop or Move up/Move down, removed, and cleared.
- [x] The image-to-PDF screen now uses explicitly selected images in the
      displayed order. The CLI retains its existing folder-based workflow.
- [x] A4 and Letter normalization is represented by the canvas in the merge
      preview before processing.
- [x] PDF-producing UI operations now generate a temporary review result.
      The destination is not replaced until **Save result** is selected;
      **Discard result** removes the staged file.
- [x] Integer and decimal spin boxes use packaged, theme-compatible up/down
      arrow icons with larger click targets.
- [x] Regression coverage was added for ordered inputs, multi-document
      preview, zoom, target canvas, staged save/discard, explicit image order,
      and spin-box resources.

## Additional fixes

- [x] Replace the platform-provided sidebar button glyph—which displayed the
      PySide6/Qt logo on some systems—with packaged show/hide sidebar icons.
- [x] Rename the complete project identity from the previous name to
      **PDFSilo**, including the Python package, imports, exception base class,
      CLI and GUI commands, application metadata, documentation, tests, and
      packaging configuration.
- [x] Replace the overly blue/navy dark workspace with neutral charcoal
      canvas, sidebar, cards, and alternate surfaces. Indigo and teal remain
      focused interaction accents.
- [x] Support System default, Light, and Dark modes, including live operating
      system appearance changes.
- [x] Replace the incorrect runtime SVG identity with the supplied
      `pdfsilo/ui/resources/logo.png` and `icon.png`. The same approved artwork
      is used in both themes.
- [x] Add useful Settings content for appearance, preview visibility,
      overwrite confirmation, opening output folders, window restoration, and
      reopening the last tool.
- [x] Label the third Settings tab consistently as **Startup and privacy** and
      document exactly which non-sensitive values PDFSilo remembers.
- [x] Add Restore defaults and ensure disabled window/navigation restoration
      removes the corresponding stored state.
- [x] Replace the generic About message with product capabilities, local-only
      privacy information, version/license details, and project support links.
- [x] Add regression tests for the color system, themes, PNG identity assets,
      settings labels and behavior, privacy allowlisting, and About content.

The resulting architecture and product decisions are documented in
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) and
[`docs/adr/`](../docs/adr/README.md).
