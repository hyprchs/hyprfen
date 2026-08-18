from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import zstandard as zstd

from hyprfen import encode_fen
from hyprfen.lichess_sample import (
    LICHESS_2013_01_FILENAME,
    LICHESS_2013_01_URL,
    collect_unique_fens_from_pgn,
    default_cache_dir,
    ensure_lichess_2013_01,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Write pinned hyprfen bitstream vectors.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=default_cache_dir())
    args = parser.parse_args()

    cache_dir = args.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    if subprocess.check_output(["git", "status", "--porcelain"], text=True, cwd=root):
        raise RuntimeError("generate vectors from a clean hyprfen worktree")

    source_path = Path(os.environ.get("HYPRFEN_LICHESS_ZST", cache_dir / LICHESS_2013_01_FILENAME))
    if not source_path.is_file() and "HYPRFEN_LICHESS_ZST" not in os.environ:
        ensure_lichess_2013_01(cache_dir)
    if not source_path.is_file():
        raise FileNotFoundError(f"the compressed Lichess source is required: {source_path}")

    reference = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=root).strip()
    source_digest = sha256(source_path)
    pgn_path = cache_dir / f"{source_path.stem}-{source_digest}.pgn"
    if not pgn_path.exists():
        temporary = pgn_path.with_suffix(pgn_path.suffix + ".part")
        dctx = zstd.ZstdDecompressor()
        with source_path.open("rb") as compressed, temporary.open("wb") as out:
            with dctx.stream_reader(compressed) as reader:
                shutil.copyfileobj(reader, out)
        temporary.replace(pgn_path)

    sample_path = cache_dir / f"first_100000_unique_fens-{source_digest}-{reference}.txt"
    if sample_path.exists():
        fens = sample_path.read_text(encoding="utf-8").splitlines()
    else:
        fens = sorted(collect_unique_fens_from_pgn(pgn_path, limit=100_000))
        with sample_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(fens) + "\n")
    if len(fens) != 100_000 or len(set(fens)) != 100_000:
        raise ValueError("expected 100000 unique FENs")

    temporary = args.output.with_suffix(args.output.suffix + ".part")
    with temporary.open("w", encoding="ascii", newline="\n") as f:
        f.write("# hyprfen bitstream compatibility vectors v1\n")
        f.write(f"# reference: hyprchs/hyprfen@{reference}\n")
        f.write(f"# source: {LICHESS_2013_01_URL}\n")
        f.write(f"# source-sha256: {source_digest}\n")
        f.write(f"# cases: {len(fens)}\n")
        for fen in fens:
            f.write(f"{fen}\t{encode_fen(fen).hex()}\n")
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
