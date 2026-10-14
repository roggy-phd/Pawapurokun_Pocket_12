# v31 silent fix: second-slot effective strength

This release changes the four existing v31 patchers **without changing their GUI or command-line options**. The change is ON by default.

- Original overlay10: `HenkaV` entry at `0x02170594` rejects pitch-selection codes `7..12`, returning a zero base strength.
- Fix: branch to 60 bytes at `0x021921C4..0x021921FF` (previously unused profiler text).
- Codes `0..6` and `13+`: retain original behavior.
- Codes `7..11`: call the existing effective-level function at `0x0216D494`, cap at 6, then continue the original post-processing.
- Code `12`: use the same speed-based strength route as code 5.
- Third/additional pitches already rewritten as first-slot codes remain unaffected.
- The base ROM is required; patchers reject already modified ROMs by SHA-1.

This changes auto-pennant behavior for all pitchers and invalidates direct controlled comparisons with earlier v31 ROMs. Keep old ROMs and data for reproducibility. Static checks of the patched overlay are not a substitute for in-game or emulator validation.
