"""
synth.py
The audio engine. Two jobs:
  1. note_to_freq() — convert a note name like "G#3" into a frequency in Hz.
  2. karplus_strong() — synthesize a plucked-string sound for that frequency.
  3. render_bar() — mix pre-rendered string plucks into one full bar of audio,
     according to the current chord + strum pattern + tempo.

Performance note: Karplus-Strong is synthesized ONCE per unique note at startup
and cached (see build_note_cache). Rendering a bar then just means copying/mixing
those cached buffers at the right sample offsets — cheap enough to do in real time,
one bar ahead, in a background thread.
"""

import re
import numpy as np

SAMPLE_RATE = 44100
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_to_freq(note: str) -> float:
    """Convert e.g. 'F#4' -> frequency in Hz, using A4 = 440Hz as reference."""
    match = re.match(r"^([A-G]#?)(\d)$", note)
    if not match:
        raise ValueError(f"Bad note name: {note}")
    name, octave = match.group(1), int(match.group(2))
    semitone_index = NOTE_NAMES.index(name)
    # Semitone distance from A4 (A, octave 4)
    semitones_from_a4 = (octave - 4) * 12 + (semitone_index - NOTE_NAMES.index("A"))
    return 440.0 * (2 ** (semitones_from_a4 / 12))


def karplus_strong(freq: float, duration: float = 0.9, decay: float = 0.996) -> np.ndarray:
    """
    Classic Karplus-Strong plucked-string synthesis:
    start from a burst of noise, repeatedly average+decay it in a feedback loop.
    That averaging acts as a simple low-pass filter, which is what makes noise
    decay into something that sounds like a struck/plucked string dying out.
    """
    n_samples = int(SAMPLE_RATE * duration)
    period_samples = max(2, int(SAMPLE_RATE / freq))

    # Ring buffer seeded with noise = the initial "pluck" excitation
    buffer = np.random.uniform(-1, 1, period_samples)
    output = np.zeros(n_samples, dtype=np.float32)

    for i in range(n_samples):
        output[i] = buffer[i % period_samples]
        # Feedback: average current sample with the next one, then decay slightly
        next_val = decay * 0.5 * (buffer[i % period_samples] + buffer[(i + 1) % period_samples])
        buffer[i % period_samples] = next_val

    # Fade out the tail so notes don't click when cut off
    fade_len = min(2000, n_samples)
    output[-fade_len:] *= np.linspace(1, 0, fade_len)
    return output


def build_note_cache(all_notes) -> dict:
    """Pre-render every note used by any chord, once, at startup."""
    return {note: karplus_strong(note_to_freq(note)) for note in all_notes}


def render_bar(chord_notes, pattern, bpm, note_cache, stagger_sec=0.018, gain=0.35) -> np.ndarray:
    """
    Build one full bar of audio for the given chord + strum pattern + tempo,
    by mixing cached plucked-string buffers at the right sample offsets.
    """
    beat_duration = 60.0 / bpm
    bar_duration = beat_duration * 4
    step_duration = bar_duration / 8
    n_samples = int(SAMPLE_RATE * bar_duration)
    bar = np.zeros(n_samples, dtype=np.float32)

    for step_index, direction in enumerate(pattern):
        if direction not in ("D", "U"):
            continue
        notes = list(reversed(chord_notes)) if direction == "U" else chord_notes
        for i, note in enumerate(notes):
            buf = note_cache[note]
            start = int((step_index * step_duration + i * stagger_sec) * SAMPLE_RATE)
            end = start + len(buf)
            if start >= n_samples:
                continue
            usable = min(end, n_samples) - start
            bar[start:start + usable] += buf[:usable] * gain

    # Prevent clipping if multiple strings/steps overlap loudly
    peak = np.max(np.abs(bar)) if np.any(bar) else 1.0
    if peak > 1.0:
        bar = bar / peak
    return bar
