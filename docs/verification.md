# Verification

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

The seven tests cover deterministic regeneration of the 432-record sample; a true zero alongside an unknown report; balanced transfers; missing monthly totals; a missing withdrawal field with an observed closing count; the 19-item closing discrepancy; duplicate and absent keys; invalid numeric text; four rendered PNGs; refusal to produce a partial current board view; and the four Tableau-ready exports, including their distinct grains and blank April total.

The repository was also copied into a clean temporary directory. The sample generator recreated the tracked ledger byte-for-byte. The analysis rebuilt all four CSV/Markdown text outputs byte-for-byte, produced four readable PNG charts, and passed the test suite in that copy. The Tableau export also recreated its four included CSVs byte-for-byte. The copy required no external files.
