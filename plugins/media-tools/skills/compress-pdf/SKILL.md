---
name: compress-pdf
description: Shrink a PDF so it's small enough to email or share, using Ghostscript to downsample and recompress the images inside it while keeping fonts and text intact. Use this whenever a PDF is too big to send — "compress this pdf", "my pdf is too large to email", "shrink this pdf under 25MB", "make this exported pdf smaller for the client", "this PDF won't attach to Gmail", or when a freshly exported/printed PDF needs to fit an attachment limit. Trigger whenever someone wants a PDF to be smaller or complains it's too big to send, even if they don't say the word "compress". For shrinking PowerPoint decks or images (not PDFs), use the compress-files skill instead.
---

# Compress PDF (for emailing)

Make a PDF small enough to send without wrecking it. This is built for the "I exported a deck to PDF and now it's 40 MB and Gmail won't take it" case, so the default is to shrink just enough to clear an attachment limit and no more.

`scripts/compress_pdf.py` drives Ghostscript. The reason Ghostscript is the right engine: almost all the weight in a big PDF is its images, and Ghostscript can *downsample* them — lower their DPI and recompress — which is where the real savings come from. Fonts stay embedded and subset, so text stays sharp and the layout doesn't move; you're trading image resolution for size, nothing else. (A tool like qpdf only does lossless stream compression and barely dents an image-heavy PDF, which is why it isn't used here.)

## Requirements

Ghostscript (`gs`) must be installed — check with `which gs`. If missing, install it (e.g. `apt-get install -y ghostscript`). `pdfinfo` (poppler) is used to verify page counts and is usually already present.

## Workflow

1. **Find the PDF.** If the user pointed at a folder, list the PDFs and their sizes so you can see which ones actually need shrinking:

   ```bash
   python scripts/compress_pdf.py --list "<folder>"
   ```

2. **Compress.** The default mode is *auto*: it lowers image quality one step at a time and stops the moment the file drops under the target size, so it sacrifices the least quality needed to make the file sendable.

   ```bash
   python scripts/compress_pdf.py "<file.pdf>"                 # target 25 MB (Gmail)
   python scripts/compress_pdf.py "<file.pdf>" --target-mb 10  # a tighter limit
   ```

   The script prints a JSON summary: original vs compressed size, the reduction percentage, which quality level it settled on, whether the target was met, and a page-count check (`pages_ok`) so a corrupted or truncated output gets caught before it goes out.

3. **Deliver.** Send the `<name>_compressed.pdf` to the user (in Cowork, `SendUserFile`). Mention the before/after sizes so they know it'll attach.

## Quality levels

Auto mode walks these from best quality downward and stops when the target is met. You can also pick one directly with `--level` when you want a fixed result rather than a size target:

- `high` — images at 200 dpi. Barely-visible quality loss; use when the file only needs to come down a little, or the client will look closely at image detail.
- `balanced` — 150 dpi (roughly "ebook" quality). The usual sweet spot for a deck going out by email.
- `small` — 110 dpi. Noticeably lighter; fine for on-screen reading.
- `tiny` — 72 dpi ("screen" quality). Smallest, but images get soft — reach for it only when the file must fit a hard limit.

Mono/black-and-white images (like scanned text) are kept at a higher resolution than colour images at every level, so text pages stay crisp even when photos are downsampled hard.

## Behaviour worth knowing

The script never hands back a file larger than the original. Some PDFs — already-optimised ones, or vector/text-heavy PDFs with little imagery — simply don't shrink; downsampling can even add overhead. When that happens the script keeps the original bytes and tells you so (`used_original_because_no_gain`), so the user is never worse off. If it can't reach the target even at `tiny`, it uses the smallest result it got and says so in a `note` — at that point the honest options are a higher target, splitting the PDF, or removing/replacing the heaviest images, and it's worth surfacing that rather than shipping a still-too-big file.

## Where this fits with the other skills

If the source is a PowerPoint deck rather than a PDF, and it's the *deck* that's oversized, the `compress-files` skill shrinks the .pptx directly. A natural client-ready chain is: `pptx-to-pdf` to export a faithful PDF, then this skill to get that PDF under the email limit. Because this skill preserves embedded fonts, it doesn't undo the fidelity work `pptx-to-pdf` does.
