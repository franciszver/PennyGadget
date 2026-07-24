"""Build demo.mp4 and demo.gif from an ordered directory of PNG screenshot frames.

Reads every ``*.png`` file in --frames-dir (sorted by filename, so name
frames ``01-login.png``, ``02-qa-math.png``, ... to control order), holds
each frame on screen for --seconds-per-frame, and writes:

  - <out-dir>/demo.mp4  (via imageio-ffmpeg's bundled ffmpeg binary)
  - <out-dir>/demo.gif  (via Pillow, downscaled to --gif-width)

Dependencies (not in requirements.txt - install before running):
    pip install imageio-ffmpeg Pillow

Usage:
    python scripts/build_demo_media.py --frames-dir _docs/local/demo-frames --out-dir demo-media
"""

import argparse
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

DEFAULT_SECONDS_PER_FRAME = 2.5
DEFAULT_FPS = 30
DEFAULT_GIF_WIDTH = 800
DEFAULT_OUT_DIR = "demo-media"


def _round_to_even(value):
    """ffmpeg's yuv420p output needs even width/height."""
    return value if value % 2 == 0 else value - 1


def load_frame_paths(frames_dir):
    frames_dir = Path(frames_dir)
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frames directory does not exist: {frames_dir}")
    paths = sorted(frames_dir.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"No PNG frames found in {frames_dir}")
    return paths


def build_mp4(frame_paths, out_path, seconds_per_frame, fps):
    first = Image.open(frame_paths[0]).convert("RGB")
    width = max(2, _round_to_even(first.width))
    height = max(2, _round_to_even(first.height))

    writer = imageio_ffmpeg.write_frames(
        str(out_path),
        (width, height),
        fps=fps,
        codec="libx264",
        pix_fmt_out="yuv420p",
    )
    writer.send(None)  # seed the generator
    hold_frames = max(1, round(seconds_per_frame * fps))
    try:
        for path in frame_paths:
            img = Image.open(path).convert("RGB")
            if img.size != (width, height):
                img = img.resize((width, height))
            frame_bytes = img.tobytes()
            for _ in range(hold_frames):
                writer.send(frame_bytes)
    finally:
        writer.close()


def build_gif(frame_paths, out_path, seconds_per_frame, gif_width):
    frames = []
    for path in frame_paths:
        img = Image.open(path).convert("RGB")
        if gif_width and img.width > gif_width:
            ratio = gif_width / img.width
            img = img.resize((gif_width, max(1, round(img.height * ratio))))
        frames.append(img)

    duration_ms = int(seconds_per_frame * 1000)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )


def build_demo_media(
    frames_dir,
    out_dir=DEFAULT_OUT_DIR,
    seconds_per_frame=DEFAULT_SECONDS_PER_FRAME,
    fps=DEFAULT_FPS,
    gif_width=DEFAULT_GIF_WIDTH,
):
    frame_paths = load_frame_paths(frames_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mp4_path = out_dir / "demo.mp4"
    gif_path = out_dir / "demo.gif"
    build_mp4(frame_paths, mp4_path, seconds_per_frame, fps)
    build_gif(frame_paths, gif_path, seconds_per_frame, gif_width)
    return mp4_path, gif_path


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--frames-dir", required=True, help="Directory of ordered PNG frames"
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help=f"Output directory for demo.mp4/demo.gif (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--seconds-per-frame",
        type=float,
        default=DEFAULT_SECONDS_PER_FRAME,
        help=f"How long each frame is held (default: {DEFAULT_SECONDS_PER_FRAME})",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=DEFAULT_FPS,
        help=f"MP4 frame rate (default: {DEFAULT_FPS})",
    )
    parser.add_argument(
        "--gif-width",
        type=int,
        default=DEFAULT_GIF_WIDTH,
        help=f"GIF output width in pixels, downscaled proportionally (default: {DEFAULT_GIF_WIDTH})",
    )
    args = parser.parse_args()

    try:
        mp4_path, gif_path = build_demo_media(
            args.frames_dir,
            args.out_dir,
            args.seconds_per_frame,
            args.fps,
            args.gif_width,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {mp4_path} ({mp4_path.stat().st_size} bytes)")
    print(f"Wrote {gif_path} ({gif_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
