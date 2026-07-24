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
import json
import shutil
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from _demo_audio import mux_audio, synth_music
from PIL import Image, ImageDraw, ImageFont

DEFAULT_SECONDS_PER_FRAME = 2.5
DEFAULT_FPS = 30
DEFAULT_GIF_WIDTH = 800
DEFAULT_OUT_DIR = "demo-media"
DEFAULT_CAPTIONS_PATH = Path(__file__).parent / "demo_captions.json"

_CAPTION_FONT_PATHS = ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf")


def _round_to_even(value):
    """ffmpeg's yuv420p output needs even width/height."""
    return value if value % 2 == 0 else value - 1


def load_captions(captions_path):
    """Load a {frame filename: caption text} mapping. Missing file -> no captions."""
    if not captions_path:
        return {}
    captions_path = Path(captions_path)
    if not captions_path.exists():
        return {}
    with open(captions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_font(size):
    for font_path in _CAPTION_FONT_PATHS:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_font(draw, text, max_width, start_size, min_size=12):
    size = max(start_size, min_size)
    font = _load_font(size)
    while size > min_size:
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            break
        size -= 2
        font = _load_font(size)
    return font


def apply_caption(img, caption):
    """Draw a semi-transparent caption bar at the bottom of img (RGB -> RGB)."""
    if not caption:
        return img
    rgba = img.convert("RGBA")
    width, height = rgba.size
    bar_height = max(1, round(height * 0.12))

    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(0, height - bar_height), (width, height)], fill=(0, 0, 0, 170))

    font = _fit_font(draw, caption, width * 0.9, start_size=max(14, bar_height // 2))
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (width - text_w) / 2 - bbox[0]
    text_y = height - bar_height + (bar_height - text_h) / 2 - bbox[1]
    draw.text((text_x, text_y), caption, font=font, fill=(255, 255, 255, 255))

    return Image.alpha_composite(rgba, overlay).convert("RGB")


def load_frame_paths(frames_dir):
    frames_dir = Path(frames_dir)
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frames directory does not exist: {frames_dir}")
    paths = sorted(frames_dir.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"No PNG frames found in {frames_dir}")
    return paths


def build_mp4(frame_paths, out_path, seconds_per_frame, fps, captions=None):
    captions = captions or {}
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
            img = apply_caption(img, captions.get(path.name))
            frame_bytes = img.tobytes()
            for _ in range(hold_frames):
                writer.send(frame_bytes)
    finally:
        writer.close()


def build_gif(frame_paths, out_path, seconds_per_frame, gif_width, captions=None):
    captions = captions or {}
    first = Image.open(frame_paths[0]).convert("RGB")
    canvas_width = first.width
    canvas_height = first.height

    frames = []
    for path in frame_paths:
        img = Image.open(path).convert("RGB")
        # Normalize to canvas size first (like build_mp4)
        if img.size != (canvas_width, canvas_height):
            img = img.resize((canvas_width, canvas_height))
        # Then downscale by gif_width
        if gif_width and img.width > gif_width:
            ratio = gif_width / img.width
            img = img.resize((gif_width, max(1, round(img.height * ratio))))
        img = apply_caption(img, captions.get(path.name))
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
    captions=None,
    music=False,
):
    frame_paths = load_frame_paths(frames_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mp4_path = out_dir / "demo.mp4"
    gif_path = out_dir / "demo.gif"
    build_mp4(frame_paths, mp4_path, seconds_per_frame, fps, captions)
    build_gif(frame_paths, gif_path, seconds_per_frame, gif_width, captions)

    if music:
        total_duration = seconds_per_frame * len(frame_paths)
        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "music.wav"
            synth_music(total_duration, audio_path)
            muxed_path = Path(tmp_dir) / "demo_with_music.mp4"
            try:
                mux_audio(mp4_path, audio_path, muxed_path)
                shutil.move(str(muxed_path), str(mp4_path))
            except Exception as exc:  # noqa: BLE001 - never lose the silent mp4
                print(
                    f"Warning: audio mux failed ({exc}); keeping silent mp4.",
                    file=sys.stderr,
                )

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
    parser.add_argument(
        "--captions",
        default=str(DEFAULT_CAPTIONS_PATH),
        help=f"JSON file mapping frame filename -> caption text (default: {DEFAULT_CAPTIONS_PATH})",
    )
    parser.add_argument(
        "--music",
        action="store_true",
        help="Mux gentle synthesized background music into demo.mp4 (gif stays silent)",
    )
    args = parser.parse_args()

    try:
        mp4_path, gif_path = build_demo_media(
            args.frames_dir,
            args.out_dir,
            args.seconds_per_frame,
            args.fps,
            args.gif_width,
            captions=load_captions(args.captions),
            music=args.music,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {mp4_path} ({mp4_path.stat().st_size} bytes)")
    print(f"Wrote {gif_path} ({gif_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
