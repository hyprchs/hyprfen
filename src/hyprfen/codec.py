from __future__ import annotations

from dataclasses import dataclass

import chess

from .bitops import pdep, pext, popcount
from .bitstream import BitReader, BitWriter


WHITE = chess.WHITE
BLACK = chess.BLACK


@dataclass(frozen=True)
class EncodeStats:
    encoded_bytes: int
    encoded_bits: int
    occupancy_count: int


class HyprfenError(ValueError):
    pass


class UnsupportedPositionError(HyprfenError):
    pass


class MalformedEncodingError(HyprfenError):
    pass


def _castling_bits(board: chess.Board) -> int:
    bits = 0
    if board.has_kingside_castling_rights(WHITE):
        bits |= 1 << 0
    if board.has_queenside_castling_rights(WHITE):
        bits |= 1 << 1
    if board.has_kingside_castling_rights(BLACK):
        bits |= 1 << 2
    if board.has_queenside_castling_rights(BLACK):
        bits |= 1 << 3
    return bits


def _castling_rights_from_bits(bits: int) -> int:
    rights = 0
    if bits & (1 << 0):
        rights |= chess.BB_H1
    if bits & (1 << 1):
        rights |= chess.BB_A1
    if bits & (1 << 2):
        rights |= chess.BB_H8
    if bits & (1 << 3):
        rights |= chess.BB_A8
    return rights


def _ep_file(board: chess.Board) -> int | None:
    if board.ep_square is None:
        return None
    return chess.square_file(board.ep_square)


def _ep_square_from_file(file_index: int, turn: bool) -> int:
    if not 0 <= file_index <= 7:
        raise MalformedEncodingError(f"invalid en-passant file: {file_index}")
    rank_index = 5 if turn == WHITE else 2
    return chess.square(file_index, rank_index)


def _validate_standard_board(board: chess.Board) -> None:
    if board.chess960:
        raise UnsupportedPositionError("Chess960 positions are not supported by this codec")
    if board.promoted:
        # Standard FEN cannot express promoted markers anyway. Reject to avoid
        # silently dropping python-chess-internal state when round-tripping a Board.
        raise UnsupportedPositionError(
            "board.promoted is non-zero; encode FEN strings instead of Board objects "
            "if you only care about standard FEN round-tripping"
        )


def encode_board(board: chess.Board) -> bytes:
    _validate_standard_board(board)

    occ = board.occupied
    white_occ = board.occupied_co[WHITE]
    pawns = board.pawns
    knights = board.knights
    bishops = board.bishops
    rooks = board.rooks
    queens = board.queens

    writer = BitWriter()
    writer.write_bits(occ, 64)

    n_occ = popcount(occ)
    writer.write_bits(pext(white_occ, occ), n_occ)
    writer.write_bits(pext(pawns, occ), n_occ)

    rem = occ & ~pawns
    writer.write_bits(pext(knights, rem), popcount(rem))
    rem &= ~knights
    writer.write_bits(pext(bishops, rem), popcount(rem))
    rem &= ~bishops
    writer.write_bits(pext(rooks, rem), popcount(rem))
    rem &= ~rooks
    writer.write_bits(pext(queens, rem), popcount(rem))

    writer.write_bool(board.turn)
    writer.write_bits(_castling_bits(board), 4)

    ep_file = _ep_file(board)
    writer.write_bool(ep_file is not None)
    if ep_file is not None:
        writer.write_bits(ep_file, 3)

    writer.write_varuint(board.halfmove_clock)
    writer.write_varuint(board.fullmove_number)

    return writer.to_bytes()


def encode_fen(fen: str) -> bytes:
    return encode_board(chess.Board(fen))


def encoding_stats(board_or_fen: chess.Board | str) -> EncodeStats:
    board = chess.Board(board_or_fen) if isinstance(board_or_fen, str) else board_or_fen
    encoded = encode_board(board)
    return EncodeStats(
        encoded_bytes=len(encoded),
        encoded_bits=_encoded_bit_length(board),
        occupancy_count=board.occupied.bit_count(),
    )


def _encoded_bit_length(board: chess.Board) -> int:
    occ = board.occupied
    pawns = board.pawns
    knights = board.knights
    bishops = board.bishops
    rooks = board.rooks
    n_occ = popcount(occ)
    total = 64 + n_occ + n_occ
    rem = occ & ~pawns
    total += popcount(rem)
    rem &= ~knights
    total += popcount(rem)
    rem &= ~bishops
    total += popcount(rem)
    rem &= ~rooks
    total += popcount(rem)
    total += 1 + 4 + 1
    if board.ep_square is not None:
        total += 3
    total += _varuint_bit_length(board.halfmove_clock)
    total += _varuint_bit_length(board.fullmove_number)
    return total


def _varuint_bit_length(value: int) -> int:
    if value < 0:
        raise ValueError("value must be non-negative")
    nbytes = 1
    while value >= 0x80:
        value >>= 7
        nbytes += 1
    return nbytes * 8


def decode_board(data: bytes) -> chess.Board:
    reader = BitReader(data)

    occ = reader.read_bits(64)
    n_occ = popcount(occ)

    white_occ = pdep(reader.read_bits(n_occ), occ)
    pawns = pdep(reader.read_bits(n_occ), occ)

    rem = occ & ~pawns
    knights = pdep(reader.read_bits(popcount(rem)), rem)
    rem &= ~knights
    bishops = pdep(reader.read_bits(popcount(rem)), rem)
    rem &= ~bishops
    rooks = pdep(reader.read_bits(popcount(rem)), rem)
    rem &= ~rooks
    queens = pdep(reader.read_bits(popcount(rem)), rem)
    kings = rem & ~queens

    turn = reader.read_bool()
    castling_bits = reader.read_bits(4)
    has_ep = reader.read_bool()
    ep_square = _ep_square_from_file(reader.read_bits(3), turn) if has_ep else None
    halfmove_clock = reader.read_varuint()
    fullmove_number = reader.read_varuint()

    # Validate that only up to 7 zero padding bits remain.
    remaining = reader.remaining_bits()
    if remaining > 7:
        raise MalformedEncodingError("too many unread bits remain after decoding")
    if remaining and reader.read_bits(remaining) != 0:
        raise MalformedEncodingError("non-zero padding bits found at end of stream")

    black_occ = occ ^ white_occ

    piece_sets = [
        (pawns & white_occ, chess.PAWN, WHITE),
        (pawns & black_occ, chess.PAWN, BLACK),
        (knights & white_occ, chess.KNIGHT, WHITE),
        (knights & black_occ, chess.KNIGHT, BLACK),
        (bishops & white_occ, chess.BISHOP, WHITE),
        (bishops & black_occ, chess.BISHOP, BLACK),
        (rooks & white_occ, chess.ROOK, WHITE),
        (rooks & black_occ, chess.ROOK, BLACK),
        (queens & white_occ, chess.QUEEN, WHITE),
        (queens & black_occ, chess.QUEEN, BLACK),
        (kings & white_occ, chess.KING, WHITE),
        (kings & black_occ, chess.KING, BLACK),
    ]

    board = chess.Board(None)
    board.clear_stack()
    for bitboard, piece_type, color in piece_sets:
        bb = bitboard
        while bb:
            lsb = bb & -bb
            square = lsb.bit_length() - 1
            board.set_piece_at(square, chess.Piece(piece_type, color))
            bb ^= lsb

    board.turn = turn
    board.castling_rights = _castling_rights_from_bits(castling_bits)
    board.ep_square = ep_square
    board.halfmove_clock = halfmove_clock
    board.fullmove_number = fullmove_number
    board.promoted = 0
    board.chess960 = False
    return board


def decode_fen(data: bytes) -> str:
    return decode_board(data).fen(en_passant="fen")
