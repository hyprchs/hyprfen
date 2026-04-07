# hyprfen

A compact, fast, reversible binary codec for **standard chess FENs** built on top of `python-chess` bitboards.

It uses this layout for piece placement:

1. 64-bit occupancy bitboard
2. white occupancy extracted through `occ`
3. pawn occupancy extracted through `occ`
4. knight occupancy extracted through `occ \ pawns`
5. bishop occupancy extracted through `occ \ pawns \ knights`
6. rook occupancy extracted through `occ \ pawns \ knights \ bishops`
7. queen occupancy extracted through `occ \ pawns \ knights \ bishops \ rooks`
8. kings are implied by the remaining occupied squares

Metadata is then appended:

- side to move: 1 bit
- castling rights: 4 bits (`KQkq`)
- en-passant: 1 presence bit + 3 file bits when present
- halfmove clock: unsigned LEB128
- fullmove number: unsigned LEB128

This keeps exact round-trip fidelity for standard FEN strings while staying very close to the structure already exposed by `python-chess`.

## Quick start

```bash
uv sync
uv run python - <<'PY'
from hyprfen import encode_fen, decode_fen

fen = "r1bqk2r/pppp1ppp/5n2/n1b1p1B1/2B1P3/2NP1Q2/PPP2PPP/R3K1NR b KQkq - 4 6"
blob = encode_fen(fen)
print(len(blob), blob.hex())
print(decode_fen(blob))
PY
```

## Cache behavior

The Lichess dump and the cached 100k-FEN sample both live in:

```text
.cache/
```

at the project root by default, so repeated `uv run pytest -q` runs do not re-download or re-decompress the database, and they can also skip rebuilding the first 100,000 unique-FEN sample once it has been written.

You can override that location with:

```bash
HYPRFEN_CACHE_DIR=/some/path uv run pytest -q
```

You can also point directly at an existing file:

```bash
HYPRFEN_LICHESS_ZST=/path/to/lichess_db_standard_rated_2013-01.pgn.zst uv run pytest -q
HYPRFEN_LICHESS_PGN=/path/to/lichess_db_standard_rated_2013-01.pgn uv run pytest -q
```

## Running tests

```bash
uv run pytest -q
```

The main round-trip test downloads the January 2013 Lichess database dump if needed, decompresses it if needed, walks through games with `python-chess`, collects the first 100,000 unique FENs, caches them locally, and verifies:

```python
fen == decode_fen(encode_fen(fen))
```

for all of them.

## Real-data size reports

Quick benchmark summary:

```bash
uv run python scripts/benchmark_lichess.py
```

More detailed report, including true encoded bit lengths, stored byte-aligned lengths, savings percentages, and occupancy distribution:

```bash
uv run python scripts/report_lichess_savings.py
```

## Notes

- This codec is for **standard chess**, not Chess960.
- It round-trips **standard FEN strings** exactly.
- `python-chess` has an internal `board.promoted` bitboard that standard FEN does not encode. For that reason, `encode_board()` rejects `Board` objects with `board.promoted != 0`. If you only care about standard FEN round-tripping, use `encode_fen()`.
