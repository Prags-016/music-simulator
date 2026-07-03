"""
gui.py
The desktop window. Kept deliberately simple for the prototype: a chord grid,
a tempo slider, a pattern dropdown, and a play/stop button — plus global keyboard
handling so the same shortcuts from the Electron version work here too
(A S D F G H J = chords, Space = play/stop, Up/Down = tempo).
"""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QComboBox
)
from PyQt6.QtCore import Qt

from chords import CHORDS, KEY_TO_CHORD, STRUM_PATTERNS
from audio_engine import AudioEngine

STYLE_SHEET = """
QMainWindow { background-color: #2b1e14; }
QWidget { color: #f2ead9; font-family: 'Segoe UI', sans-serif; }
QLabel#chordDisplay { font-size: 44px; font-weight: bold; color: #e3b45c; }
QLabel#status { color: #b8a88f; font-size: 12px; }
QPushButton {
    background-color: #3f2c1d; border: 1px solid #5a4128; border-radius: 8px;
    padding: 14px; font-size: 16px; font-weight: bold;
}
QPushButton:hover { border-color: #c8963e; }
QPushButton#chordActive { border-color: #e3b45c; background-color: #5a4128; }
QPushButton#playBtn { background-color: #c8963e; color: #2b1e14; font-size: 15px; }
QPushButton#playBtn:hover { background-color: #e3b45c; }
QComboBox, QSlider { padding: 4px; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Strummer (Python prototype)")
        self.resize(560, 620)
        self.setStyleSheet(STYLE_SHEET)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # so keyPressEvent fires

        self.engine = AudioEngine()
        self.engine.chord_changed.connect(self.on_chord_changed)

        self.chord_buttons = {}
        self._build_ui()
        self.on_chord_changed(self.engine.current_chord)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Guitar Strummer")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Press A S D F G H J to switch chords. Space to play/stop.")
        subtitle.setStyleSheet("color: #b8a88f; font-size: 12px;")
        layout.addWidget(subtitle)

        # Now-playing display
        self.chord_display = QLabel("-")
        self.chord_display.setObjectName("chordDisplay")
        self.chord_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.chord_display)

        self.status_label = QLabel("Stopped")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Controls row
        controls = QHBoxLayout()
        self.tempo_slider = QSlider(Qt.Orientation.Horizontal)
        self.tempo_slider.setMinimum(50)
        self.tempo_slider.setMaximum(180)
        self.tempo_slider.setValue(100)
        self.tempo_slider.valueChanged.connect(self.on_tempo_changed)
        self.tempo_label = QLabel("Tempo: 100 BPM")

        self.pattern_combo = QComboBox()
        for key, val in STRUM_PATTERNS.items():
            self.pattern_combo.addItem(val["label"], userData=key)
        self.pattern_combo.currentIndexChanged.connect(self.on_pattern_changed)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setObjectName("playBtn")
        self.play_btn.clicked.connect(self.toggle_playback)

        tempo_box = QVBoxLayout()
        tempo_box.addWidget(self.tempo_label)
        tempo_box.addWidget(self.tempo_slider)
        controls.addLayout(tempo_box, stretch=2)

        pattern_box = QVBoxLayout()
        pattern_box.addWidget(QLabel("Strum pattern"))
        pattern_box.addWidget(self.pattern_combo)
        controls.addLayout(pattern_box, stretch=2)

        controls.addWidget(self.play_btn, stretch=1)
        layout.addLayout(controls)

        # Chord grid
        layout.addWidget(QLabel("Chords"))
        grid = QGridLayout()
        for i, (key, chord_key) in enumerate(KEY_TO_CHORD.items()):
            btn = QPushButton(f"{key.upper()}\n{chord_key}")
            btn.clicked.connect(lambda checked, c=chord_key: self.engine.request_chord(c))
            grid.addWidget(btn, i // 4, i % 4)
            self.chord_buttons[chord_key] = btn
        layout.addLayout(grid)

        layout.addStretch()

    # ---- Engine callbacks ----
    def on_chord_changed(self, chord_key: str):
        self.chord_display.setText(chord_key)
        for key, btn in self.chord_buttons.items():
            btn.setObjectName("chordActive" if key == chord_key else "")
            btn.style().unpolish(btn)
            btn.style().polish(btn)  # force Qt to re-evaluate the stylesheet for this button

    # ---- UI event handlers ----
    def on_tempo_changed(self, value):
        self.engine.set_bpm(value)
        self.tempo_label.setText(f"Tempo: {value} BPM")

    def on_pattern_changed(self, index):
        pattern_key = self.pattern_combo.itemData(index)
        self.engine.set_pattern(pattern_key)

    def toggle_playback(self):
        if self.engine._playing:
            self.engine.stop_playback()
            self.play_btn.setText("▶ Play")
            self.status_label.setText("Stopped")
        else:
            self.engine.start_playback()
            self.play_btn.setText("■ Stop")
            self.status_label.setText("Playing")

    # ---- Keyboard shortcuts (mirrors the Electron version's controls) ----
    def keyPressEvent(self, event):
        key = event.text().lower()
        if key in KEY_TO_CHORD:
            self.engine.request_chord(KEY_TO_CHORD[key])
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_playback()
        elif event.key() == Qt.Key.Key_Up:
            self.tempo_slider.setValue(min(180, self.tempo_slider.value() + 5))
        elif event.key() == Qt.Key.Key_Down:
            self.tempo_slider.setValue(max(50, self.tempo_slider.value() - 5))
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
