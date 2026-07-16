#!/usr/bin/env python3
"""Convert a video (or a time range of it) into an animated GIF using ffmpeg.

Uses a two-pass palette workflow (palettegen + paletteuse) so colours stay
clean and the file stays reasonably small — a plain one-pass GIF export looks
noticeably worse for the same size.

Examples
--------
List the videos in a folder:
    python video_to_gif.py --list ~/Downloads/clips

Convert seconds 3 to 8 of a clip at balanced quality:
    python video_to_gif.py input.mp4 --start 3 --end 8

Override size / frame rate explicitly:
    python video_to_gif.py input.mp4 --start 0 --end 5 --width 600 --fps 18
"""
import argparse
import json
import os
import subprocess
import sys

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".mpg", ".mpeg", ".3gp", ".ts"}

# (width, fps) presets. width caps the output; height scales proportionally.
PRESETS = {
    "balanced": (480, 15),
    "high": (720, 20),
    "small": (320, 10),
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe_duration(path):
    """Return video duration in seconds, or None if it can't be read."""
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def list_videos(folder):
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        print(f"Not a folder: {folder}", file=sys.stderr)
        sys.exit(1)
    rows = []
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and os.path.splitext(name)[1].lower() in VIDEO_EXTS:
            dur = ffprobe_duration(p)
            rows.append({"file": name, "path": p,
                         "duration_seconds": round(dur, 2) if dur else None})
    print(json.dumps({"folder": folder, "videos": rows}, ensure_ascii=False, indent=2))
    return rows


def human_size(nbytes):
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024 or unit == "GB":
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024


def convert(args):
    src = os.path.expanduser(args.input)
    if not os.path.isfile(src):
        print(f"File not found: {src}", file=sys.stderr)
        sys.exit(1)

    duration_total = ffprobe_duration(src)
    start = float(args.start)
    if args.end is not None:
        end = float(args.end)
    elif duration_total is not None:
        end = duration_total
    else:
        print("Could not determine video length; please pass --end.", file=sys.stderr)
        sys.exit(1)

    if end <= start:
        print(f"--end ({end}) must be greater than --start ({start}).", file=sys.stderr)
        sys.exit(1)
    if duration_total is not None and start >= duration_total:
        print(f"--start ({start}s) is past the end of the video ({duration_total:.2f}s).", file=sys.stderr)
        sys.exit(1)
    length = end - start

    width, fps = PRESETS[args.quality]
    if args.width is not None:
        width = args.width
    if args.fps is not None:
        fps = args.fps

    if args.output:
        out = os.path.expanduser(args.output)
    else:
        base = os.path.splitext(src)[0]
        out = f"{base}_{int(round(start))}-{int(round(end))}s.gif"
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)

    palette = out + ".palette.png"
    # -2 keeps height even; harmless for GIF and avoids odd-dimension warnings.
    scale = f"scale={width}:-2:flags=lanczos"
    vf_gen = f"fps={fps},{scale},palettegen=stats_mode=diff"
    vf_use = f"fps={fps},{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"

    # Pass 1: build an optimal 256-colour palette for this clip.
    r1 = run(["ffmpeg", "-y", "-ss", str(start), "-t", str(length), "-i", src,
              "-vf", vf_gen, palette])
    if r1.returncode != 0:
        print("Palette generation failed:\n" + r1.stderr[-2000:], file=sys.stderr)
        sys.exit(1)

    # Pass 2: render the GIF using that palette.
    r2 = run(["ffmpeg", "-y", "-ss", str(start), "-t", str(length), "-i", src,
              "-i", palette, "-lavfi", vf_use,
              "-loop", "0" if args.loop else "-1", out])
    if os.path.exists(palette):
        os.remove(palette)
    if r2.returncode != 0:
        print("GIF encoding failed:\n" + r2.stderr[-2000:], file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(out)
    result = {
        "output": out,
        "start_seconds": start,
        "end_seconds": end,
        "clip_length_seconds": round(length, 2),
        "width": width,
        "fps": fps,
        "quality_preset": args.quality,
        "size_bytes": size,
        "size_human": human_size(size),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser(description="Convert a video (or a time range) to an animated GIF.")
    ap.add_argument("input", nargs="?", help="Path to the source video.")
    ap.add_argument("--list", metavar="FOLDER", help="List video files in a folder (with durations) and exit.")
    ap.add_argument("--start", type=float, default=0.0, help="Start time in seconds (default 0).")
    ap.add_argument("--end", type=float, default=None, help="End time in seconds (default: end of video).")
    ap.add_argument("--quality", choices=list(PRESETS), default="balanced",
                    help="Quality preset (default balanced: 480px / 15fps).")
    ap.add_argument("--width", type=int, default=None, help="Override output width in px (height auto).")
    ap.add_argument("--fps", type=int, default=None, help="Override frame rate.")
    ap.add_argument("--output", help="Output .gif path (default: alongside the source).")
    ap.add_argument("--loop", action="store_true", default=True, help="Loop forever (default).")
    ap.add_argument("--no-loop", dest="loop", action="store_false", help="Play once, do not loop.")
    args = ap.parse_args()

    if args.list:
        list_videos(args.list)
        return
    if not args.input:
        ap.error("provide a video path, or use --list FOLDER to see available videos.")
    convert(args)


if __name__ == "__main__":
    main()
