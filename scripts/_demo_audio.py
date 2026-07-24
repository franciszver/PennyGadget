"""Synthesize a gentle background-music WAV track and mux it into an mp4.

Pure stdlib (wave + math + array) — no numpy, no soundfont. The "instrument"
is a plain sine wave with a short attack/decay envelope per note, arpeggiated
over a calm four-chord major progression (C - G - Am - F). Used by
scripts/build_demo_media.py to add a low-volume, non-annoying music bed to
the generated demo.mp4 (the .gif stays silent).
"""

import array
import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg

SAMPLE_RATE = 44100
DEFAULT_AMPLITUDE = 0.15  # keep quiet: headroom under int16 full-scale, no clipping
DEFAULT_NOTE_DURATION = 0.45  # seconds per arpeggio note

# MIDI note numbers per chord, arpeggiated low -> high.
# C major (C3 E3 G3 C4) - G major (G3 B3 D4 G4) - A minor (A3 C4 E4 A4) - F major (F3 A3 C4 F4)
_PROGRESSION_MIDI = [
    (48, 52, 55, 60),
    (55, 59, 62, 67),
    (57, 60, 64, 69),
    (53, 57, 60, 65),
]


def _midi_to_freq(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def _note_samples(freq, num_samples, amplitude):
    """One sine-wave note with a short linear attack/decay envelope (click-free)."""
    ramp = max(1, min(num_samples // 6, int(SAMPLE_RATE * 0.03)))
    out = [0.0] * num_samples
    for i in range(num_samples):
        value = math.sin(2 * math.pi * freq * (i / SAMPLE_RATE))
        if i < ramp:
            value *= i / ramp
        elif i >= num_samples - ramp:
            value *= (num_samples - i) / ramp
        out[i] = value * amplitude
    return out


def synth_music(
    duration_seconds,
    out_path,
    note_duration=DEFAULT_NOTE_DURATION,
    amplitude=DEFAULT_AMPLITUDE,
):
    """Write a calm, arpeggiated WAV track (mono, 16-bit, 44.1kHz) to out_path."""
    out_path = Path(out_path)
    total_samples = max(1, int(duration_seconds * SAMPLE_RATE))
    note_samples_count = max(1, int(note_duration * SAMPLE_RATE))

    track = []
    chord_idx = 0
    while len(track) < total_samples:
        chord = _PROGRESSION_MIDI[chord_idx % len(_PROGRESSION_MIDI)]
        for note in chord:
            track.extend(
                _note_samples(_midi_to_freq(note), note_samples_count, amplitude)
            )
            if len(track) >= total_samples:
                break
        chord_idx += 1
    track = track[:total_samples]

    # Short overall fade-in/out so the track doesn't start or stop abruptly.
    fade_samples = min(len(track) // 4, int(SAMPLE_RATE * 1.0))
    for i in range(fade_samples):
        gain = i / fade_samples
        track[i] *= gain
        track[-(i + 1)] *= gain

    pcm = array.array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in track))

    with wave.open(str(out_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm.tobytes())

    return out_path


def mux_audio(video_path, audio_path, out_path, ffmpeg_exe=None):
    """Mux audio_path into video_path (video re-encode-free) and write out_path."""
    ffmpeg_exe = ffmpeg_exe or imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg audio mux failed (exit {result.returncode}): "
            f"{result.stderr.decode(errors='replace')}"
        )
    return Path(out_path)
