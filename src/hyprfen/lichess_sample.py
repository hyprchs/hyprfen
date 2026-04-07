from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path

import chess.pgn
import zstandard as zstd

LICHESS_2013_01_URL = "https://database.lichess.org/standard/lichess_db_standard_rated_2013-01.pgn.zst"
LICHESS_2013_01_FILENAME = "lichess_db_standard_rated_2013-01.pgn.zst"
LICHESS_2013_01_PGN_FILENAME = "lichess_db_standard_rated_2013-01.pgn"
FEN_SAMPLE_FILENAME_TEMPLATE = "first_{limit}_unique_fens.txt"


def default_cache_dir() -> Path:
    env_cache_dir = os.environ.get("HYPRFEN_CACHE_DIR")
    if env_cache_dir:
        return Path(env_cache_dir)

    project_root = Path(__file__).resolve().parents[3]
    return project_root / ".cache"


def ensure_lichess_2013_01(cache_dir: Path | None = None) -> Path:
    cache_dir = default_cache_dir() if cache_dir is None else cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    env_pgn = os.environ.get("HYPRFEN_LICHESS_PGN")
    if env_pgn:
        return Path(env_pgn)

    zst_path = cache_dir / LICHESS_2013_01_FILENAME
    pgn_path = cache_dir / LICHESS_2013_01_PGN_FILENAME

    env_zst = os.environ.get("HYPRFEN_LICHESS_ZST")
    if env_zst:
        zst_path = Path(env_zst)

    if not zst_path.exists() and not pgn_path.exists():
        tmp_path = zst_path.with_suffix(zst_path.suffix + ".part")
        request = urllib.request.Request(
            LICHESS_2013_01_URL,
            headers={"User-Agent": "hyprfen-test/0.1 (+https://openai.com)"},
        )
        with urllib.request.urlopen(request) as response, tmp_path.open("wb") as out:
            shutil.copyfileobj(response, out)
        tmp_path.replace(zst_path)

    if not pgn_path.exists():
        tmp_path = pgn_path.with_suffix(pgn_path.suffix + ".part")
        dctx = zstd.ZstdDecompressor()
        with zst_path.open("rb") as compressed, tmp_path.open("wb") as out:
            with dctx.stream_reader(compressed) as reader:
                shutil.copyfileobj(reader, out)
        tmp_path.replace(pgn_path)

    return pgn_path


def _sample_cache_path(cache_dir: Path, limit: int) -> Path:
    return cache_dir / FEN_SAMPLE_FILENAME_TEMPLATE.format(limit=limit)


def collect_unique_fens_from_pgn(pgn_path: Path, limit: int = 100_000) -> set[str]:
    if limit <= 0:
        return set()

    unique_fens: set[str] = set()

    with pgn_path.open("r", encoding="utf-8", errors="replace") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            board = game.board()
            unique_fens.add(board.fen(en_passant="fen"))
            if len(unique_fens) >= limit:
                break

            for move in game.mainline_moves():
                board.push(move)
                unique_fens.add(board.fen(en_passant="fen"))
                if len(unique_fens) >= limit:
                    break

            if len(unique_fens) >= limit:
                break

    return unique_fens


def load_or_create_unique_fen_sample(limit: int = 100_000, cache_dir: Path | None = None) -> list[str]:
    if limit <= 0:
        return []

    cache_dir = default_cache_dir() if cache_dir is None else cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    sample_path = _sample_cache_path(cache_dir, limit)

    if sample_path.exists():
        with sample_path.open("r", encoding="utf-8") as f:
            fens = [line.rstrip("\n") for line in f]
        if len(fens) == limit:
            return fens

    pgn_path = ensure_lichess_2013_01(cache_dir)
    unique_fens = collect_unique_fens_from_pgn(pgn_path, limit=limit)
    if len(unique_fens) != limit:
        raise ValueError(f"expected {limit} unique FENs, got {len(unique_fens)}")

    fens = sorted(unique_fens)
    tmp_path = sample_path.with_suffix(sample_path.suffix + ".part")
    with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
        for fen in fens:
            f.write(fen)
            f.write("\n")
    tmp_path.replace(sample_path)
    return fens
