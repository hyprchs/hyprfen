from __future__ import annotations

import pytest

from hyprfen import decode_fen, encode_fen
from hyprfen.lichess_sample import load_or_create_unique_fen_sample


@pytest.fixture(scope="session")
def first_100k_unique_fens() -> list[str]:
    return load_or_create_unique_fen_sample(limit=100_000)


def test_roundtrip_first_100k_unique_fens(first_100k_unique_fens: list[str]) -> None:
    for fen in first_100k_unique_fens:
        encoded = encode_fen(fen)
        decoded = decode_fen(encoded)
        assert decoded == fen


def test_average_encoded_size_is_smaller_than_raw(first_100k_unique_fens: list[str]) -> None:
    raw_total = 0
    encoded_total = 0
    for fen in first_100k_unique_fens:
        raw_total += len(fen.encode("ascii"))
        encoded_total += len(encode_fen(fen))

    avg_raw = raw_total / len(first_100k_unique_fens)
    avg_encoded = encoded_total / len(first_100k_unique_fens)

    assert avg_encoded < avg_raw
    assert avg_encoded <= 32.0
