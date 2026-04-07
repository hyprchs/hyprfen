from __future__ import annotations

from collections import Counter

from hyprfen import encoding_stats
from hyprfen.lichess_sample import load_or_create_unique_fen_sample


def main() -> None:
    fens = load_or_create_unique_fen_sample(limit=100_000)

    raw_total_bits = 0
    encoded_total_bits = 0
    encoded_total_stored_bits = 0
    occupancy_counter: Counter[int] = Counter()
    encoded_bits_counter: Counter[int] = Counter()
    raw_bytes_counter: Counter[int] = Counter()

    for fen in fens:
        raw_bits = len(fen.encode("ascii")) * 8
        stats = encoding_stats(fen)

        raw_total_bits += raw_bits
        encoded_total_bits += stats.encoded_bits
        encoded_total_stored_bits += stats.encoded_bytes * 8
        occupancy_counter[stats.occupancy_count] += 1
        encoded_bits_counter[stats.encoded_bits] += 1
        raw_bytes_counter[len(fen)] += 1

    n = len(fens)
    avg_raw_bits = raw_total_bits / n
    avg_encoded_bits = encoded_total_bits / n
    avg_encoded_stored_bits = encoded_total_stored_bits / n

    print("=== aggregate ===")
    print(f"positions:                       {n:,}")
    print(f"avg raw ASCII bits:              {avg_raw_bits:.2f}")
    print(f"avg encoded true bits:           {avg_encoded_bits:.2f}")
    print(f"avg encoded stored bits:         {avg_encoded_stored_bits:.2f}")
    print(f"avg raw ASCII bytes:             {avg_raw_bits / 8.0:.2f}")
    print(f"avg encoded stored bytes:        {avg_encoded_stored_bits / 8.0:.2f}")
    print(f"true-bit savings:                {avg_raw_bits - avg_encoded_bits:.2f} bits / position")
    print(f"stored-bit savings:              {avg_raw_bits - avg_encoded_stored_bits:.2f} bits / position")
    print(f"true-bit savings pct:            {100.0 * (1.0 - (avg_encoded_bits / avg_raw_bits)):.2f}%")
    print(f"stored-bit savings pct:          {100.0 * (1.0 - (avg_encoded_stored_bits / avg_raw_bits)):.2f}%")
    print(f"byte-alignment overhead:         {avg_encoded_stored_bits - avg_encoded_bits:.2f} bits / position")

    print("\n=== most common raw FEN lengths (bytes) ===")
    for raw_len, count in raw_bytes_counter.most_common(10):
        print(f"{raw_len:>3} bytes : {count:>7} positions ({100.0 * count / n:5.2f}%)")

    print("\n=== most common encoded true lengths (bits) ===")
    for nbits, count in encoded_bits_counter.most_common(15):
        print(f"{nbits:>3} bits  : {count:>7} positions ({100.0 * count / n:5.2f}%)")

    print("\n=== occupancy distribution ===")
    for occ in sorted(occupancy_counter):
        count = occupancy_counter[occ]
        print(f"{occ:>2} pieces : {count:>7} positions ({100.0 * count / n:5.2f}%)")


if __name__ == "__main__":
    main()
