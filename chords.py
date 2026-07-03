"""
chords.py
Music data: which notes make up each chord, which keyboard key selects which chord,
and the strumming patterns available. This mirrors chords.js from the Electron
version 1:1 so the two versions stay conceptually identical.
"""

# Standard open-position guitar chords, written as note name + octave
# (e.g. "G2" = the G below middle C's octave). Order = low string to high string.
CHORDS = {
    "G":  {"name": "G Major",          "notes": ["G2", "B2", "D3", "G3", "B3", "G4"]},
    "C":  {"name": "C Major",          "notes": ["C3", "E3", "G3", "C4", "E4"]},
    "D":  {"name": "D Major",          "notes": ["D3", "A3", "D4", "F#4"]},
    "Em": {"name": "E Minor",          "notes": ["E2", "B2", "E3", "G3", "B3", "E4"]},
    "Am": {"name": "A Minor",          "notes": ["A2", "E3", "A3", "C4", "E4"]},
    "F":  {"name": "F Major (easy)",   "notes": ["F3", "A3", "C4", "F4"]},
    "Dm": {"name": "D Minor",          "notes": ["D3", "A3", "D4", "F4"]},
}

# Physical keyboard key -> chord. Sits under the left hand for quick switching.
KEY_TO_CHORD = {
    "a": "G",
    "s": "C",
    "d": "D",
    "f": "Em",
    "g": "Am",
    "h": "F",
    "j": "Dm",
}

# Each pattern = 8 slots = the 8 eighth-note subdivisions of one 4/4 bar.
# "D" = down strum, "U" = up strum, "-" = rest.
STRUM_PATTERNS = {
    "basicDown":    {"label": "All Downs (simple)",       "pattern": ["D", "-", "D", "-", "D", "-", "D", "-"]},
    "popRock":      {"label": "Pop/Rock (D-D-U-U-D-U)",   "pattern": ["D", "-", "D", "U", "U", "D", "U", "-"]},
    "folk":         {"label": "Folk (D-DU-UDU)",          "pattern": ["D", "-", "D", "U", "-", "U", "D", "U"]},
    "reggaeSkank":  {"label": "Reggae-ish (offbeat)",     "pattern": ["-", "U", "-", "U", "-", "U", "-", "U"]},
}

# Every unique note used anywhere above, so the synth engine knows what to pre-render.
ALL_NOTES = sorted({note for chord in CHORDS.values() for note in chord["notes"]})
