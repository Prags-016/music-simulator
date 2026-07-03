# Guitar Strummer — Python Prototype

A Python/PyQt6 prototype of the same app described in the project report:
select guitar chords and a strum pattern via keyboard, hear it played back live,
in time, with chord changes cleanly quantized to the next bar.

This version exists to prototype and learn the logic in a language you're already
comfortable with. See `PYTHON_TO_JS_NOTES.md` for how this maps onto (and differs
from) the Electron/Tone.js version, when you're ready to rebuild it there.

## Setup

Requires Python 3.10+ and, on Linux, the PortAudio system library:

```bash
# Linux only — PyQt6 and sounddevice need these system packages
sudo apt-get install libportaudio2 libxcb-cursor0

pip install -r requirements.txt
python main.py
```

On macOS/Windows, `pip install -r requirements.txt` alone should be enough.

## How to use it

Same controls as the Electron version:
- Click a chord button, or press its key (**A S D F G H J**)
- **Space** to play/stop
- **↑ / ↓** to change tempo
- Dropdown to change strum pattern

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Entry point |
| `gui.py` | PyQt6 window: layout, keyboard handling, wiring buttons to the engine |
| `audio_engine.py` | Background playback thread: bar-by-bar loop, quantized chord changes |
| `synth.py` | Karplus-Strong plucked-string synthesis + bar rendering/mixing |
| `chords.py` | Chord/keyboard/pattern data (mirrors chords.js from the JS version) |

## How this version's timing works (different from the JS version)

Tone.js has a built-in musical clock to schedule individual notes precisely.
Python doesn't have an equivalent, and naive timers drift too much for tight
rhythm. So this version takes a different approach: it **pre-renders one full
bar of audio at a time** (all the strums already mixed together), plays that
whole bar with a blocking call, and only checks for a pending chord/tempo/pattern
change right before rendering the *next* bar. Same musical result (clean
quantized changes), different mechanism under the hood.

## Known limitations (prototype)

- Small gap possible between bars (a few ms) since each bar is played with a
  separate blocking call rather than one continuous audio stream — a true
  gapless version would use `sounddevice`'s streaming callback API instead.
- Karplus-Strong synthesis is a Python loop per note — fine since notes are
  cached once at startup, but renders take a moment on first launch.
- Same musical scope as v1 of the JS version: 7 open chords, 4 patterns, guitar only.
