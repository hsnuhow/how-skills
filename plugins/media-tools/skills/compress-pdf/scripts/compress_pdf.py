#!/usr/bin/env python3
"""Shrink a PDF so it's easy to email, using Ghostscript.

Ghostscript is the right tool here because the bulk of a heavy PDF is almost
always its images, and Ghostscript can *downsample* them (drop their DPI) and
recompress them — something a lossless tool like qpdf can't do. Fonts stay
embedded and subset, so text and layout are preserved; only image resolution
is traded for size.

Two ways to use it:

  * Auto (default): keep lowering image quality one step at a time until the
    file fits under a target size (default 25 MB, the Gmail attachment limit),
    then stop — so you lose the least quality needed to make it sendable.
  * Fixed level: pick a specific quality (high / balanced / small / tiny).

Examples
--------
    python compress_pdf.py deck.pdf                     # auto -> under 25 MB
    python compress_pdf.py deck.pdf --target-mb 10      # auto -> under 10 MB
    python compress_pdf.py deck.pdf --level balanced    # fixed 150 dpi
    python compress_pdf.py --list ~/Exports             # list PDFs + sizes
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

# Each level sets the DPI that colour/greyscale images are downsampled to.
# Mono (1-bit, e.g. scanned text) is kept higher so text stays crisp.
LEVELS = {
    "high":     {"color": 200, "mono": 600, "base": "/printer"},
    "balanced": {"color": 150, "mono": 600, "base": "/ebook"},
    "small":    {"color": 110, "mono": 400, "base": "/ebook"},
    "tiny":     {"color": 72,  "mono": 300, "base": "/screen"},
}
# Order the auto mode walks: best quality first, stop as soon as it fits.
LADDER = ["high", "balanced", "small", "tiny"]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def gs_bin():
    for n in ("gs", "gswin64c", "gswin32c"):
        if shutil.which(n):
            return n
    return None


def human(nbytes):
    n = float(nbytes)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024


def list_pdfs(folder):
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        print(f"Not a folder: {folder}", file=sys.stderr)
        sys.exit(1)
    rows = []
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and name.lower().endswith(".pdf"):
            rows.append({"file": name, "path": p,
                         "size_bytes": os.path.getsize(p),
                         "size_human": human(os.path.getsize(p))})
    print(json.dumps({"folder": folder, "pdfs": rows}, ensure_ascii=False, indent=2))
    return rows


def compress_once(gs, src, dst, level):
    spec = LEVELS[level]
    cmd = [
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS={spec['base']}",
        "-dNOPAUSE", "-dQUIET", "-dBATCH", "-dSAFER",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true", "-dSubsetFonts=true", "-dEmbedAllFonts=true",
        "-dColorImageDownsampleType=/Bicubic", f"-dColorImageResolution={spec['color']}",
        "-dGrayImageDownsampleType=/Bicubic", f"-dGrayImageResolution={spec['color']}",
        "-dMonoImageDownsampleType=/Subsample", f"-dMonoImageResolution={spec['mono']}",
        "-dDownsampleColorImages=true", "-dDownsampleGrayImages=true", "-dDownsampleMonoImages=true",
        f"-sOutputFile={dst}", src,
    ]
    r = run(cmd)
    return r.returncode == 0 and os.path.isfile(dst), r


def page_count(path):
    if shutil.which("pdfinfo"):
        r = run(["pdfinfo", path])
        import re
        m = re.search(r"Pages:\s+(\d+)", r.stdout)
        if m:
            return int(m.group(1))
    try:
        import pypdf
        return len(pypdf.PdfReader(path).pages)
    except Exception:
        return None


def compress(args):
    gs = gs_bin()
    if not gs:
        print("Ghostscript (gs) is not installed. Install it, e.g. "
              "`apt-get install -y ghostscript`.", file=sys.stderr)
        sys.exit(1)

    src = os.path.expanduser(args.input)
    if not os.path.isfile(src):
        print(f"File not found: {src}", file=sys.stderr)
        sys.exit(1)
    orig = os.path.getsize(src)

    if args.output:
        out = os.path.expanduser(args.output)
    else:
        base, ext = os.path.splitext(os.path.expanduser(src))
        outdir = os.path.expanduser(args.outdir) if args.outdir else os.path.dirname(os.path.abspath(src))
        out = os.path.join(outdir, os.path.basename(base) + "_compressed.pdf")
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)

    target_bytes = int(args.target_mb * 1024 * 1024) if args.target_mb else None
    src_pages = page_count(src)

    attempts = []
    chosen_level = None
    best_tmp = None

    if args.level != "auto":
        levels_to_try = [args.level]
    else:
        levels_to_try = LADDER

    for lvl in levels_to_try:
        tmp = out + f".{lvl}.tmp"
        ok, r = compress_once(gs, src, tmp, lvl)
        if not ok:
            attempts.append({"level": lvl, "ok": False,
                             "error": (r.stderr or r.stdout or "gs failed")[-500:]})
            continue
        sz = os.path.getsize(tmp)
        attempts.append({"level": lvl, "size_bytes": sz, "size_human": human(sz)})
        # Keep the smallest successful attempt as a fallback.
        if best_tmp is None or sz < os.path.getsize(best_tmp):
            if best_tmp and best_tmp != tmp and os.path.exists(best_tmp):
                os.remove(best_tmp)
            best_tmp = tmp
        else:
            os.remove(tmp)
        # Auto mode: stop at the first level that meets the target.
        if args.level == "auto" and target_bytes and sz <= target_bytes:
            chosen_level = lvl
            break

    if best_tmp is None:
        print(json.dumps({"success": False, "error": "all compression attempts failed",
                          "attempts": attempts}, ensure_ascii=False, indent=2))
        sys.exit(1)

    if chosen_level is None:
        # Either fixed-level mode, or target never met -> use the smallest result.
        chosen_level = min(attempts, key=lambda a: a.get("size_bytes", 1 << 62))["level"]

    comp_size = os.path.getsize(best_tmp)

    # Safety net: never hand back something bigger than the original. Some PDFs
    # (already-optimised, or vector-heavy with little imagery) don't shrink;
    # in that case keep the original bytes so the user is never worse off.
    used_original = False
    if comp_size >= orig:
        shutil.copyfile(src, out)
        os.remove(best_tmp)
        used_original = True
        final_size = orig
    else:
        os.replace(best_tmp, out)
        final_size = comp_size
    # Clean up any leftover tmp files from other levels.
    for a in attempts:
        for lvl in [a["level"]]:
            leftover = out + f".{lvl}.tmp"
            if os.path.exists(leftover):
                os.remove(leftover)

    out_pages = page_count(out)
    target_met = (target_bytes is None) or (final_size <= target_bytes)

    result = {
        "success": True,
        "output": out,
        "original_size_bytes": orig,
        "original_size_human": human(orig),
        "compressed_size_bytes": final_size,
        "compressed_size_human": human(final_size),
        "reduction_percent": round((1 - final_size / orig) * 100, 1) if orig else 0,
        "level_used": chosen_level,
        "target_mb": args.target_mb,
        "target_met": target_met,
        "used_original_because_no_gain": used_original,
        "pages_in": src_pages,
        "pages_out": out_pages,
        "pages_ok": (src_pages == out_pages) if (src_pages and out_pages) else None,
        "attempts": attempts,
    }
    if not target_met:
        result["note"] = (
            f"Could not get under {args.target_mb} MB even at the most aggressive "
            f"level ({human(final_size)}). Consider a higher --target-mb, splitting "
            f"the PDF, or removing large images."
        )
    if result["pages_ok"] is False:
        result["warning"] = (
            f"Page count changed ({src_pages} -> {out_pages}). Inspect the output "
            f"before sending."
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser(description="Compress a PDF for easy emailing (Ghostscript).")
    ap.add_argument("input", nargs="?", help="Path to the source PDF.")
    ap.add_argument("--list", metavar="FOLDER", help="List PDFs in a folder with sizes and exit.")
    ap.add_argument("--target-mb", type=float, default=25.0,
                    help="Target max size in MB for auto mode (default 25 = Gmail limit).")
    ap.add_argument("--level", choices=["auto"] + list(LEVELS), default="auto",
                    help="auto (shrink until under target) or a fixed quality level.")
    ap.add_argument("--outdir", help="Output folder (default: alongside the source).")
    ap.add_argument("--output", help="Explicit output path (default: <name>_compressed.pdf).")
    args = ap.parse_args()

    if args.list:
        list_pdfs(args.list)
        return
    if not args.input:
        ap.error("provide a PDF path, or use --list FOLDER.")
    compress(args)


if __name__ == "__main__":
    main()
