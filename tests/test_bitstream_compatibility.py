from __future__ import annotations

import os
from pathlib import Path

import pytest

from hyprfen import decode_fen, encode_fen


def test_bitstream_compatibility() -> None:
    vector_path = os.environ.get("HYPRFEN_BITSTREAM_VECTORS")
    if vector_path is None:
        pytest.skip("set HYPRFEN_BITSTREAM_VECTORS to run the conformance corpus")

    cases = 0
    with Path(vector_path).open(encoding="ascii") as f:
        for line_number, line in enumerate(f, start=1):
            if line.startswith("#"):
                continue
            fen, expected_hex = line.rstrip("\n").split("\t")
            expected = bytes.fromhex(expected_hex)
            assert decode_fen(expected) == fen, f"Python decode mismatch at line {line_number}"
            assert encode_fen(fen) == expected, f"Python encode mismatch at line {line_number}"
            assert decode_fen(encode_fen(fen)) == fen, f"Python round-trip mismatch at line {line_number}"
            cases += 1
    assert cases == 100_000
