# Python → JS/Electron: what carries over, what doesn't

When you're ready to rebuild this properly in Electron (see the
`guitar-strummer/` JS version and its Project Report PDF), here's what
transfers directly vs. what needs to be re-thought.

## Transfers directly (just re-expressed in JS)
- **Chord data** (`chords.py` → `chords.js`): same notes, same keyboard mapping,
  same strum patterns. This is just syntax translation.
- **The quantization concept**: "queue a chord change, apply it at the start of
  the next bar" is identical in both versions — only the mechanism differs (see below).
- **The strum-stagger idea**: triggering notes a few milliseconds apart, in
  order, to simulate a pick moving across strings.
- **UI structure**: chord grid, tempo slider, pattern dropdown, play button —
  same layout, same keyboard shortcuts.

## Does NOT transfer — needs a different approach in JS
- **Timing mechanism**: the Python version pre-renders whole bars and plays them
  with a blocking call. The JS version instead uses Tone.Transport/Tone.Sequence
  to schedule individual notes against a shared clock — a fundamentally
  different (and more precise/gapless) approach. Don't try to port the
  bar-rendering code; use Tone.js's scheduling model instead.
- **Sound synthesis**: the Python version hand-rolls Karplus-Strong in numpy.
  The JS version uses Tone.PluckSynth, which already implements the same
  algorithm internally — no need to reimplement it.
- **Threading model**: Python uses a QThread for playback. Electron's renderer
  is single-threaded JS with an event loop; Tone.js's Web Audio backend handles
  timing precision without you managing threads at all.

## Suggested order when you rebuild
1. Confirm the chord/pattern/keyboard data is identical between both versions
   (copy the values, not the code).
2. Build the JS UI first (already done in `guitar-strummer/`).
3. Wire up Tone.js scheduling using the *concept* you validated in Python
   (quantized chord changes, staggered strums) but written the "Tone.js way,"
   as shown in `renderer.js`.
