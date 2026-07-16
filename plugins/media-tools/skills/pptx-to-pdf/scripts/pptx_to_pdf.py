#!/usr/bin/env python3
"""Convert a presentation to PDF with LibreOffice at maximum fidelity.

Fidelity when sending a deck to a client hinges almost entirely on FONTS. If a
font used in the deck isn't available to the converter, LibreOffice silently
substitutes another face and the layout shifts — text reflows, lines break in
new places, boxes overflow. So this script does three things:

  1. Installs any fonts EMBEDDED in the .pptx (PowerPoint's "Embed fonts in the
     file" option) so the deck renders with its own fonts.
  2. Reports which referenced fonts are still missing from the system, so you
     can warn the user before the PDF goes out.
  3. Exports with font embedding turned on, so the fonts travel inside the PDF
     and render identically on the client's machine.

Usage
-----
    python pptx_to_pdf.py deck.pptx                 # -> deck.pdf beside it
    python pptx_to_pdf.py deck.pptx --outdir out/   # choose output folder
    python pptx_to_pdf.py --list "~/Presentations"  # list decks in a folder
    python pptx_to_pdf.py --check-fonts deck.pptx   # font report only, no PDF
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

PRES_EXTS = {".pptx", ".ppt", ".potx", ".odp", ".key"}
FONT_MAGIC_EXTS = (".ttf", ".otf", ".ttc")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def soffice_bin():
    for name in ("soffice", "libreoffice"):
        if shutil.which(name):
            return name
    return None


def list_presentations(folder):
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        print(f"Not a folder: {folder}", file=sys.stderr)
        sys.exit(1)
    rows = []
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and os.path.splitext(name)[1].lower() in PRES_EXTS:
            rows.append({"file": name, "path": p,
                         "size_bytes": os.path.getsize(p)})
    print(json.dumps({"folder": folder, "presentations": rows}, ensure_ascii=False, indent=2))
    return rows


# Metric-compatible substitutes bundled with LibreOffice. If the substitute is
# installed, the missing original is NOT a fidelity risk — the glyph metrics
# match, so text occupies the same space and the layout does not shift.
METRIC_COMPATIBLE = {
    "arial": ["Liberation Sans", "Arimo"],
    "helvetica": ["Liberation Sans", "Arimo"],
    "times new roman": ["Liberation Serif", "Tinos"],
    "times": ["Liberation Serif", "Tinos"],
    "courier new": ["Liberation Mono", "Cousine"],
    "calibri": ["Carlito"],
    "cambria": ["Caladea"],
}


def referenced_fonts(pptx_path):
    """Font families the deck actually puts on text.

    Only two sources count: typefaces set explicitly on runs inside the slides,
    and the theme's major/minor Latin fonts (the default heading/body faces).
    The rest of a theme XML lists dozens of per-script language fallbacks
    (Angsana New, DaunPenh, ...) that are never used — scanning the whole
    document would flag all of them and make the report useless.
    """
    fonts = set()
    try:
        with zipfile.ZipFile(pptx_path) as z:
            names = z.namelist()
            # 1) Explicit typefaces on real content (slides + their masters/layouts).
            for n in names:
                low = n.lower()
                if re.search(r"ppt/(slides|slidelayouts|slidemasters)/[^/]+\.xml$", low):
                    xml = z.read(n).decode("utf-8", "ignore")
                    for m in re.findall(r'typeface="([^"]+)"', xml):
                        if m and not m.startswith("+"):
                            fonts.add(m)
            # 2) Theme major/minor Latin fonts only (skip the script-fallback list).
            for n in names:
                if re.search(r"ppt/theme/theme\d+\.xml$", n.lower()):
                    xml = z.read(n).decode("utf-8", "ignore")
                    for block in re.findall(r"<a:(?:majorFont|minorFont)>(.*?)</a:(?:majorFont|minorFont)>", xml, re.S):
                        m = re.search(r'<a:latin[^>]*typeface="([^"]+)"', block)
                        if m and m.group(1) and not m.group(1).startswith("+"):
                            fonts.add(m.group(1))
    except zipfile.BadZipFile:
        pass  # .ppt (binary) or non-zip; can't introspect
    return sorted(fonts)


def expected_slide_count(pptx_path):
    """How many slides SHOULD appear in the PDF.

    That's the count in the presentation's slide-id list (the real running
    order), minus any slide flagged hidden (show="0"), since LibreOffice and
    PowerPoint both exclude hidden slides from a PDF export. Returns None for
    formats we can't introspect (e.g. legacy binary .ppt).
    """
    try:
        with zipfile.ZipFile(pptx_path) as z:
            names = z.namelist()
            pres_name = "ppt/presentation.xml"
            if pres_name not in names:
                return None
            pres = z.read(pres_name).decode("utf-8", "ignore")
            rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8", "ignore")
            rid_target = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
            order_rids = re.findall(r"<p:sldId[^>]*r:id=\"([^\"]+)\"", pres)
            count = 0
            for rid in order_rids:
                target = rid_target.get(rid, "")
                slide_name = "ppt/" + target.lstrip("/").replace("../", "")
                if slide_name not in names:
                    slide_name = "ppt/slides/" + target.split("/")[-1]
                hidden = False
                if slide_name in names:
                    head = z.read(slide_name)[:400].decode("utf-8", "ignore")
                    hidden = bool(re.match(r"<p:sld\b[^>]*\bshow=\"0\"", head))
                if not hidden:
                    count += 1
            return count
    except (zipfile.BadZipFile, KeyError):
        return None


def pdf_page_count(pdf_path):
    """Page count of the produced PDF, via whatever tool is available."""
    try:
        import pypdf
        return len(pypdf.PdfReader(pdf_path).pages)
    except Exception:
        pass
    if shutil.which("pdfinfo"):
        r = run(["pdfinfo", pdf_path])
        m = re.search(r"Pages:\s+(\d+)", r.stdout)
        if m:
            return int(m.group(1))
    return None


def installed_font_families():
    r = run(["fc-list", ":", "family"])
    fams = set()
    for line in r.stdout.splitlines():
        for part in line.split(","):
            fams.add(part.strip().lower())
    return fams


def extract_embedded_fonts(pptx_path, dest_dir):
    """Copy fonts embedded inside the pptx (ppt/fonts/*) into dest_dir.

    In OOXML the embedded font parts are plain TrueType/OpenType files, so they
    can be dropped straight into a font directory. Returns the list installed.
    """
    installed = []
    try:
        with zipfile.ZipFile(pptx_path) as z:
            for n in z.namelist():
                low = n.lower()
                if "/fonts/" in low or low.startswith("fonts/"):
                    data = z.read(n)
                    # Sniff the magic so we only keep real font files.
                    if data[:4] in (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"):
                        base = os.path.basename(n) or "embedded"
                        if not base.lower().endswith(FONT_MAGIC_EXTS):
                            base += ".ttf"
                        out = os.path.join(dest_dir, base)
                        with open(out, "wb") as f:
                            f.write(data)
                        installed.append(base)
    except zipfile.BadZipFile:
        pass
    return installed


def font_report(pptx_path, embedded_installed):
    """Classify each referenced font by fidelity risk.

    - available: the font (or an embedded copy) is present -> renders as designed.
    - safe_substitution: a metric-compatible substitute is installed -> layout
      is preserved even though the face name differs; not a fidelity risk.
    - missing: no match and no compatible substitute -> WILL shift layout.
    """
    refs = referenced_fonts(pptx_path)
    have = installed_font_families()
    embedded_lower = {os.path.splitext(e)[0].lower() for e in embedded_installed}

    available, safe, missing = [], [], []
    for f in refs:
        fl = f.lower()
        if fl in have or any(fl in e or e in fl for e in embedded_lower):
            available.append(f)
            continue
        subs = METRIC_COMPATIBLE.get(fl, [])
        matched = next((s for s in subs if s.lower() in have), None)
        if matched:
            safe.append({"font": f, "substitute": matched})
        else:
            missing.append(f)
    return {
        "referenced_fonts": refs,
        "available_fonts": available,
        "safe_substitutions": safe,
        "missing_fonts": missing,
    }


def convert(pptx_path, outdir, install_fonts=True):
    soffice = soffice_bin()
    if not soffice:
        print("LibreOffice (soffice) is not installed. Install it, e.g. "
              "`apt-get install -y libreoffice`.", file=sys.stderr)
        sys.exit(1)

    src = os.path.expanduser(pptx_path)
    if not os.path.isfile(src):
        print(f"File not found: {src}", file=sys.stderr)
        sys.exit(1)
    outdir = os.path.expanduser(outdir) if outdir else os.path.dirname(os.path.abspath(src))
    os.makedirs(outdir, exist_ok=True)

    # Use a throwaway HOME so we can drop embedded fonts into ~/.fonts and give
    # LibreOffice a clean, lock-free user profile in one shot.
    tmp_home = tempfile.mkdtemp(prefix="pptx2pdf_home_")
    font_dir = os.path.join(tmp_home, ".fonts")
    os.makedirs(font_dir, exist_ok=True)

    embedded = []
    if install_fonts:
        embedded = extract_embedded_fonts(src, font_dir)
        if embedded:
            run(["fc-cache", "-f", font_dir], env={**os.environ, "HOME": tmp_home})

    report = font_report(src, embedded)

    env = {**os.environ, "HOME": tmp_home}
    profile = "file://" + os.path.join(tmp_home, "louser")
    # impress_pdf_Export filter with font embedding on -> fonts ride inside the PDF.
    pdf_filter = ('pdf:impress_pdf_Export:'
                  '{"EmbedStandardFonts":{"type":"boolean","value":"true"}}')
    cmd = [soffice, "--headless", "--norestore", "--nolockcheck",
           f"-env:UserInstallation={profile}",
           "--convert-to", pdf_filter, "--outdir", outdir, src]
    r = run(cmd, env=env)

    base = os.path.splitext(os.path.basename(src))[0]
    out_pdf = os.path.join(outdir, base + ".pdf")
    ok = os.path.isfile(out_pdf)

    shutil.rmtree(tmp_home, ignore_errors=True)

    # Content check: did every slide make it into the PDF? LibreOffice can
    # silently drop a slide it fails to render (complex/heavily-layered slides),
    # and a short PDF sent to a client is a serious error — so verify counts.
    expected = expected_slide_count(src) if ok else None
    pages = pdf_page_count(out_pdf) if ok else None
    content_ok = None
    content_warning = None
    if expected is not None and pages is not None:
        content_ok = (pages == expected)
        if not content_ok:
            content_warning = (
                f"PDF has {pages} pages but the deck has {expected} slides "
                f"({expected - pages} missing). LibreOffice likely failed to render "
                f"a slide. Do NOT send this to a client as-is — see which slide is "
                f"missing and fix that slide, or export the PDF from PowerPoint itself."
            )

    result = {
        "success": ok,
        "output": out_pdf if ok else None,
        "size_bytes": os.path.getsize(out_pdf) if ok else None,
        "expected_slides": expected,
        "pdf_pages": pages,
        "content_ok": content_ok,
        "embedded_fonts_installed": embedded,
        "referenced_fonts": report["referenced_fonts"],
        "available_fonts": report["available_fonts"],
        "safe_substitutions": report["safe_substitutions"],
        "missing_fonts": report["missing_fonts"],
    }
    if content_warning:
        result["content_warning"] = content_warning
    if not ok:
        result["error"] = (r.stderr or r.stdout or "conversion failed")[-2000:]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not ok:
        sys.exit(1)
    return result


def main():
    ap = argparse.ArgumentParser(description="Convert a presentation to PDF with LibreOffice, preserving fonts/layout.")
    ap.add_argument("input", nargs="?", help="Path to the presentation (.pptx/.ppt/.odp/...).")
    ap.add_argument("--list", metavar="FOLDER", help="List presentations in a folder and exit.")
    ap.add_argument("--outdir", help="Output folder (default: alongside the source file).")
    ap.add_argument("--check-fonts", action="store_true",
                    help="Only report referenced/missing fonts; do not convert.")
    ap.add_argument("--no-install-fonts", dest="install_fonts", action="store_false",
                    help="Skip installing fonts embedded inside the pptx before converting.")
    args = ap.parse_args()

    if args.list:
        list_presentations(args.list)
        return
    if not args.input:
        ap.error("provide a presentation path, or use --list FOLDER.")

    if args.check_fonts:
        src = os.path.expanduser(args.input)
        tmp = tempfile.mkdtemp(prefix="fontcheck_")
        embedded = extract_embedded_fonts(src, tmp)
        rep = font_report(src, embedded)
        rep["embedded_fonts_in_file"] = embedded
        shutil.rmtree(tmp, ignore_errors=True)
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return

    convert(args.input, args.outdir, install_fonts=args.install_fonts)


if __name__ == "__main__":
    main()
