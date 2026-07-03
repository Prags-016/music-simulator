"""
audio_engine.py
Runs playback on a background thread (as a QThread) so the GUI never freezes.

Key design decision vs. the JS/Tone.js version:
Tone.js can schedule individual notes against a shared musical clock. Python has
no equivalent built in, and naive timers drift too much for tight rhythm. So
instead, this engine renders one FULL BAR of audio ahead of time, then plays it
with a blocking call — and only checks for a pending chord/pattern/tempo change
right before rendering the *next* bar. That's what gives the same "changes land
cleanly on the next bar" behavior as the Electron version, just via a different
mechanism (pre-rendered buffers instead of live-scheduled notes).
"""

import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

from chords import CHORDS, STRUM_PATTERNS, ALL_NOTES
from synth import SAMPLE_RATE, build_note_cache, render_bar


class AudioEngine(QThread):
    chord_changed = pyqtSignal(str)   # emitted when a queued chord change lands
    bar_started = pyqtSignal(int)     # emitted at the start of each bar (for future beat UI)

    def __init__(self):
        super().__init__()
        self.note_cache = build_note_cache(ALL_NOTES)  # pre-render all notes once, at startup
        self.current_chord = "G"
        self.pending_chord = None
        self.pattern_key = "popRock"
        self.bpm = 100
        self._playing = False
        self._bar_count = 0

    # ---- Public control methods (safe to call from the GUI thread) ----
    def request_chord(self, chord_key: str):
        if chord_key not in CHORDS:
            return
        if self._playing:
            self.pending_chord = chord_key  # queued, applied at next bar
        else:
            self.current_chord = chord_key
            self.chord_changed.emit(self.current_chord)

    def set_pattern(self, pattern_key: str):
        if pattern_key in STRUM_PATTERNS:
            self.pattern_key = pattern_key

    def set_bpm(self, bpm: int):
        self.bpm = max(50, min(180, bpm))

    def start_playback(self):
        self._playing = True
        if not self.isRunning():
            self.start()  # QThread.start() -> calls run() on a new thread

    def stop_playback(self):
        self._playing = False
        sd.stop()  # cut audio immediately rather than waiting for the current bar to finish

    # ---- The actual playback loop (runs on the background thread) ----
    def run(self):
        while self._playing:
            # Apply any queued chord change now, at the top of the bar
            if self.pending_chord:
                self.current_chord = self.pending_chord
                self.pending_chord = None
                self.chord_changed.emit(self.current_chord)

            self._bar_count += 1
            self.bar_started.emit(self._bar_count)

            chord_notes = CHORDS[self.current_chord]["notes"]
            pattern = STRUM_PATTERNS[self.pattern_key]["pattern"]
            bar_audio = render_bar(chord_notes, pattern, self.bpm, self.note_cache)

            if not self._playing:
                break
            sd.play(bar_audio, SAMPLE_RATE, blocking=True)  # blocks until the bar finishes
