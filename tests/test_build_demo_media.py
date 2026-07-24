"""Tests for scripts/build_demo_media.py.

Validates the screenshots -> mp4/gif pipeline against synthetic frames
(solid-color PNGs), since real app screenshots require a live browser
session. See scripts/build_demo_media.py and _docs/DEMO-script.md.
"""

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_demo_media import build_demo_media, load_frame_paths  # noqa: E402


def _make_frames(tmp_path, count=3, size=(1280, 720)):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    colors = [(200, 0, 0), (0, 200, 0), (0, 0, 200)]
    for i in range(count):
        img = Image.new("RGB", size, colors[i % len(colors)])
        img.save(frames_dir / f"{i:02d}-frame.png")
    return frames_dir


def test_build_demo_media_produces_mp4_and_gif(tmp_path):
    frames_dir = _make_frames(tmp_path, count=3)
    out_dir = tmp_path / "out"

    mp4_path, gif_path = build_demo_media(
        frames_dir, out_dir, seconds_per_frame=0.2, fps=10, gif_width=400
    )

    assert mp4_path.exists()
    assert mp4_path.stat().st_size > 0

    assert gif_path.exists()
    assert gif_path.stat().st_size > 0

    with Image.open(gif_path) as gif:
        assert gif.is_animated
        assert gif.n_frames == 3


def test_build_demo_media_handles_odd_dimensions(tmp_path):
    frames_dir = _make_frames(tmp_path, count=2, size=(1281, 721))
    out_dir = tmp_path / "out"

    mp4_path, gif_path = build_demo_media(
        frames_dir, out_dir, seconds_per_frame=0.2, fps=10, gif_width=400
    )

    assert mp4_path.exists()
    assert mp4_path.stat().st_size > 0
    assert gif_path.exists()
    assert gif_path.stat().st_size > 0


def test_load_frame_paths_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_frame_paths(tmp_path / "does-not-exist")


def test_load_frame_paths_empty_dir_raises(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        load_frame_paths(empty_dir)
