from __future__ import annotations

from hyprfen import encode_fen, encoding_stats
from hyprfen.lichess_sample import load_or_create_unique_fen_sample


def main() -> None:
    fens = load_or_create_unique_fen_sample(limit=100_000)

    raw_total_bytes = 0
    encoded_total_bytes = 0
    encoded_total_bits = 0
    for fen in fens:
        raw_total_bytes += len(fen.encode("ascii"))
        encoded = encode_fen(fen)
        encoded_total_bytes += len(encoded)
        encoded_total_bits += encoding_stats(fen).encoded_bits

    avg_raw_bytes = raw_total_bytes / len(fens)
    avg_raw_bits = avg_raw_bytes * 8.0
    avg_encoded_bytes = encoded_total_bytes / len(fens)
    avg_encoded_bits = encoded_total_bits / len(fens)

    print(f"positions:                    {len(fens):,}")
    print(f"avg raw FEN bytes:            {avg_raw_bytes:.2f}")
    print(f"avg raw FEN bits:             {avg_raw_bits:.2f}")
    print(f"avg encoded stored bytes:     {avg_encoded_bytes:.2f}")
    print(f"avg encoded stored bits:      {avg_encoded_bytes * 8.0:.2f}")
    print(f"avg encoded true bits:        {avg_encoded_bits:.2f}")
    print(f"byte savings:                 {avg_raw_bytes - avg_encoded_bytes:.2f} bytes / position")
    print(f"true bit savings:             {avg_raw_bits - avg_encoded_bits:.2f} bits / position")
    print(f"stored-byte savings:          {100.0 * (1.0 - (avg_encoded_bytes / avg_raw_bytes)):.2f}%")
    print(f"true-bit savings:             {100.0 * (1.0 - (avg_encoded_bits / avg_raw_bits)):.2f}%")
    print(f"padding overhead:             {(avg_encoded_bytes * 8.0) - avg_encoded_bits:.2f} bits / position")


if __name__ == "__main__":
    main()
