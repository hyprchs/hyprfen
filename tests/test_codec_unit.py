from __future__ import annotations

import chess

from hyprfen import decode_fen, encode_fen


def test_sample_fen_roundtrip() -> None:
    fen = "r1bqk2r/pppp1ppp/5n2/n1b1p1B1/2B1P3/2NP1Q2/PPP2PPP/R3K1NR b KQkq - 4 6"
    assert decode_fen(encode_fen(fen)) == fen


def test_en_passant_roundtrip() -> None:
    fen = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
    assert decode_fen(encode_fen(fen)) == fen


def test_randomish_mainline_roundtrip() -> None:
    board = chess.Board()
    san_moves = [
        "e4",
        "c5",
        "Nf3",
        "d6",
        "d4",
        "cxd4",
        "Nxd4",
        "Nf6",
        "Nc3",
        "a6",
        "Bg5",
        "e6",
        "f4",
        "Be7",
        "Qf3",
        "Qc7",
        "O-O-O",
        "Nbd7",
        "Bd3",
        "b5",
    ]
    for san in san_moves:
        fen = board.fen(en_passant="fen")
        assert decode_fen(encode_fen(fen)) == fen
        board.push_san(san)

    fen = board.fen(en_passant="fen")
    assert decode_fen(encode_fen(fen)) == fen
