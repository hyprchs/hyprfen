from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from pathlib import Path

from hyprfen import encode_fen
from hyprfen.lichess_sample import (
    LICHESS_2013_01_FILENAME,
    LICHESS_2013_01_URL,
    default_cache_dir,
    ensure_lichess_2013_01,
    load_or_create_unique_fen_sample,
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
    ensure_lichess_2013_01(cache_dir)
    source_path = Path(os.environ.get("HYPRFEN_LICHESS_ZST", cache_dir / LICHESS_2013_01_FILENAME))
    if not source_path.is_file():
        raise FileNotFoundError(f"the compressed Lichess source is required: {source_path}")

    fens = load_or_create_unique_fen_sample(limit=100_000, cache_dir=cache_dir)
    reference = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, cwd=Path(__file__).resolve().parents[1]
    ).strip()
    temporary = args.output.with_suffix(args.output.suffix + ".part")
    with temporary.open("w", encoding="ascii", newline="\n") as f:
        f.write("# hyprfen bitstream compatibility vectors v1\n")
        f.write(f"# reference: hyprchs/hyprfen@{reference}\n")
        f.write(f"# source: {LICHESS_2013_01_URL}\n")
        f.write(f"# source-sha256: {sha256(source_path)}\n")
        f.write(f"# cases: {len(fens)}\n")
        for fen in fens:
            f.write(f"{fen}\t{encode_fen(fen).hex()}\n")
    temporary.replace(args.output)


if __name__ == "__main__":
    main()
