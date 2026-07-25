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

[] ![Here the logo of pysides6 isntead of sidebar show/hide icons please fix](image-5.png)
[] The name of this whole project changed from safepdf to PDFSilo, change this in all the project