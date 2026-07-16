---
name: pptx-to-pdf
description: Convert a PowerPoint or other presentation (.pptx, .ppt, .potx, .odp, .key) into a high-fidelity PDF using LibreOffice, with fonts embedded and layout preserved — the reliable way to prepare a deck to send to a client. Use this whenever the user wants to turn slides or a presentation into a PDF, "export my deck as pdf", "convert this pptx to pdf for a client", "save my slides as a pdf to email", "make a pdf of the presentation with the fonts intact", or convert a whole folder of presentations to PDF. Trigger whenever a presentation needs to become a PDF, even if the user doesn't say the exact word "convert" — especially when they care about the result looking correct or are sending it to someone.
---

# Presentation to PDF (client-ready)

Convert a deck to PDF so that what the client opens looks exactly like what was designed — right fonts, right layout, nothing reflowed. This is aimed at the "I need to email these slides to a customer and they must look right" case, so fidelity is the priority.

`scripts/pptx_to_pdf.py` wraps LibreOffice's headless PDF export and adds the two things that actually protect fidelity: it installs any fonts embedded inside the .pptx before converting, and it turns on font embedding in the exported PDF so those fonts travel with the file.

## Why fonts are the whole game

Layout in a presentation is glued to its fonts. If a font used in the deck isn't available to the converter, LibreOffice substitutes a different one, and the substitute has different letter widths — so text reflows, lines wrap differently, and text boxes overflow or leave gaps. The PDF then looks subtly (or badly) wrong compared to the original. Everything below exists to prevent that.

Two safeguards handle it:

- **Embedded fonts get installed first.** If the deck was saved with PowerPoint's "Embed fonts in the file" option, the font files live inside the .pptx. The script extracts them and makes them available to LibreOffice for the conversion, so the deck renders in its own typefaces.
- **The export embeds fonts into the PDF.** The fonts are written into the PDF itself, so the file renders identically on the client's computer even if they don't have those fonts.

## Requirements

LibreOffice (`soffice`) must be installed — check with `which soffice`. If missing, install it (e.g. `apt-get install -y libreoffice`). `fc-list`/`fc-cache` (fontconfig) are used for the font handling and are normally present alongside LibreOffice.

## Workflow

1. **Find the deck.** If the user named a folder, list the presentations in it:

   ```bash
   python scripts/pptx_to_pdf.py --list "<folder>"
   ```

2. **Check fonts first (recommended for client work).** Before committing to the PDF, see whether any referenced font is missing from the system and not embedded in the file:

   ```bash
   python scripts/pptx_to_pdf.py --check-fonts "<deck.pptx>"
   ```

   The report sorts every font the deck actually uses into three buckets:

   - `available_fonts` — installed (or embedded in the file). Render as designed.
   - `safe_substitutions` — a metric-compatible substitute is installed (e.g. Arial→Liberation Sans, Calibri→Carlito, Times New Roman→Liberation Serif). The glyph widths match, so the layout does **not** shift. This is safe; you don't need to warn the user about these.
   - `missing_fonts` — no match and no compatible substitute. These are the real fidelity risk: LibreOffice will substitute something with different metrics and the layout can shift.

   So the check you care about is simple: **if `missing_fonts` is empty, fidelity will be solid** (safe substitutions are fine). If `missing_fonts` lists anything, flag those specific fonts to the user and see "When fonts are missing" below — this is exactly what makes a client-facing PDF look off.

   Note: the report only lists fonts the deck genuinely uses (explicit fonts on the slides plus the theme's heading/body fonts); it deliberately ignores the long list of language-fallback fonts baked into every Office theme, so a clean report really is clean.

3. **Convert.**

   ```bash
   python scripts/pptx_to_pdf.py "<deck.pptx>"
   ```

   Add `--outdir "<folder>"` to choose where the PDF lands. The script prints a JSON summary with the output path, file size, which embedded fonts it installed, and any fonts that were still missing.

4. **Check the result — page count first.** The script automatically compares the PDF's page count against the deck's real slide count (running order, minus hidden slides) and reports `content_ok`. This matters because LibreOffice can *silently drop a slide it fails to render* — complex, heavily-layered slides (many stacked images/effects) are the usual victims — and a client PDF that's missing a slide is a serious error the font report won't catch. If `content_ok` is false (a `content_warning` will explain), do **not** send the PDF as-is: identify the missing slide (align slide text against PDF page text to find where the sequence skips) and either simplify/fix that slide and reconvert, or export that deck from PowerPoint itself, which renders it faithfully. Beyond the count, for a client-facing deck it's still worth opening the PDF and spot-checking a text-heavy or tightly-laid-out slide against the original to confirm nothing shifted.

5. **Deliver.** Send the PDF to the user (in Cowork, `SendUserFile`), and if they wanted it saved on their computer, write it back to their folder.

## When fonts are missing

If `missing_fonts` isn't empty, the cleanest fix is to make the deck carry its own fonts, then reconvert:

- Ask the user to re-save the .pptx from PowerPoint with **File → Options → Save → "Embed fonts in the file"** ticked. The script will then install those embedded fonts automatically and fidelity is restored.
- Or, if you have the actual font files (.ttf/.otf), install them on the system (drop them in a font directory and run `fc-cache -f`) and reconvert.

Only when neither is possible, proceed with substitution — but tell the user which fonts were substituted so there are no surprises when the client opens it.

## About GIFs, video, and animation

A standard PDF is a static, print-oriented format: it has no timeline, so animated GIFs, embedded video, slide transitions, and build animations cannot play inside it. Each animated element is rendered as a single still frame (generally its first/poster frame). This is a limitation of the PDF format itself, not of the conversion — so if a deck leans on motion, set that expectation with the user. When the point of sending it is a faithful, self-contained, printable document the client can open anywhere, PDF is the right target and this fidelity-first conversion is what you want. If they specifically need the motion preserved, that's a different deliverable (e.g. sharing the .pptx itself, or exporting the deck to video), not a PDF.

## Smaller files for email

The fidelity-first PDF embeds fonts and keeps image quality high, so it can be sizeable. If it needs to fit under an email limit (Gmail is 25 MB), don't drop fidelity blindly — first compress the media inside the file. The `compress-files` skill recompresses images inside a PDF while keeping it openable and correct; reach for that if the client-ready PDF comes out too large to attach.
