---
name: video-to-gif
description: Convert a video file (or a chosen time range of it) from a folder into an animated GIF. Use this whenever the user wants to turn a video, clip, screen recording, or movie file (.mp4, .mov, .webm, .mkv, .avi, etc.) into a GIF — including phrasings like "make a gif from this video", "turn my screen recording into a gif", "grab seconds 5 to 10 of this clip as a gif", "convert the videos in my Downloads folder to gifs", or "loop this bit of footage as a gif". Always trigger when someone mentions creating, exporting, or trimming a GIF out of video footage, even if they don't say the word "convert".
---

# Video to GIF

Turn a video, or just a slice of one, into a clean animated GIF. The user picks the start and end seconds; this skill trims and encodes that range.

The heavy lifting is done by `scripts/video_to_gif.py`, which wraps `ffmpeg` with a two-pass palette workflow (`palettegen` + `paletteuse`). That two-pass approach is what keeps colours clean and file size sane — a naive single-pass GIF export looks banded and washed out at the same size, so always use the script rather than a hand-rolled one-liner.

## Requirements

`ffmpeg` and `ffprobe` must be on the PATH. Check with `which ffmpeg ffprobe`. If missing, install via the system package manager (e.g. `apt-get install -y ffmpeg`) before proceeding.

## Workflow

1. **Find the video.** If the user pointed at a folder rather than a specific file, list what's there so they can choose and so you learn each clip's length:

   ```bash
   python scripts/video_to_gif.py --list "<folder>"
   ```

   This prints each video file with its duration in seconds — which is exactly what the user needs in order to pick a sensible start/end.

2. **Confirm the trim range.** The whole point of this skill is letting the user choose *which part* of the video becomes the GIF. If they haven't already given start and end seconds, ask for them (offer the full clip as the default). Knowing the duration from step 1, you can sanity-check that the range fits inside the clip. A few seconds usually makes the best GIF; if the user asks for a very long range, it's worth mentioning the file will be large.

3. **Convert.**

   ```bash
   python scripts/video_to_gif.py "<video>" --start <sec> --end <sec>
   ```

   The script prints a JSON summary including the output path and the final file size.

4. **Deliver.** Send the resulting `.gif` to the user (in Cowork, use `SendUserFile`). GIFs render inline, so they can preview the animation immediately. If the file came out larger than expected for how they intend to share it, offer to re-run at a smaller preset.

## Quality presets

The default is **balanced**, which the skill was tuned for: about 480px wide at 15fps — a good middle ground of sharpness and file size for most uses. Pick a different preset with `--quality` when the context calls for it:

- `balanced` — 480px, 15fps. The default; suitable for most sharing.
- `high` — 720px, 20fps. Crisper motion and detail, but a bigger file. Use when visual quality matters more than size.
- `small` — 320px, 10fps. Smallest file; good for chat apps (Line, Messenger, Slack) or tight email limits.

For fine control, override the preset with `--width <px>` and/or `--fps <n>`. Lower width and fps are the two biggest levers on file size — reach for them first if a GIF needs to shrink. By default the GIF loops forever; pass `--no-loop` to play it once.

## Notes on the time range

Start and end are in seconds and may be decimals (e.g. `--start 2.5 --end 6.25`). The script seeks with `-ss`/`-t`, so trimming is fast even on long source videos. If the user omits `--end`, it runs to the end of the clip; if they omit `--start`, it begins at 0. The end must be greater than the start, and the start must fall within the clip — the script validates this and reports a clear error otherwise.

## Batch conversions

To convert several clips (or several ranges of one clip), just call the script once per output. When making many GIFs at once, tell the user the total combined size — a folder of GIFs adds up quickly.
