# hyprfen

`hyprfen` stores standard chess FENs in about **64.9% fewer bits** than raw FEN strings on a 100,000-position real-game sample from Lichess.

It is a compact, reversible binary codec for standard chess positions. You give it a FEN string, it gives you bytes, and `decode_fen()` returns the exact original FEN.

## Format

The encoding stores:

- piece placement as bitboard-derived occupancy data
- side to move
- castling rights
- en-passant file when present
- halfmove clock
- fullmove number

Consumers do not need to know the bit layout to use it; the important property is that the codec preserves the full standard FEN string exactly.

## Reliability

The reconstruction test suite validates exact round-tripping over **100,000 unique real FENs** collected from the **Lichess January 2013 standard rated database dump**:

- source dump: [database.lichess.org](https://database.lichess.org)
- file used by the tests: `lichess_db_standard_rated_2013-01.pgn.zst`
- check performed for every sampled position: `decode_fen(encode_fen(fen)) == fen`

The tests also assert that the average encoded size is smaller than raw FEN on that dataset.

## Usage

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

Run the tests with:

```bash
uv run pytest -q
```
