# JLC order files: essential build

Same board as the full build. Upload `hellen64_NA6_94-d-gerber.zip`, then
`hellen64_NA6_94-d-BOM-essential.csv` and `hellen64_NA6_94-d-CPL.csv`.

Left off compared with the full parts list (regenerate with `tools/make_essential_bom.py`):
- on-board wideband (wbo module: U600-U604, Q600/Q601, its passives and LEDs). Use an
  external wideband controller on CAN or a 0-5 V input (pin 3N) instead;
- U5 electronic-throttle H-bridge (only needed for drive-by-wire);
- SD card socket J450 and its parts (log over USB instead).

All of these can be added to a later order; their footprints are still on the board.
