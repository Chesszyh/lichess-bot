#!/usr/bin/env python3
"""Build a Polyglot book from lichess-org/chess-openings TSV files."""

from __future__ import annotations

import argparse
import csv
import re
import struct
import sys
from collections import Counter
from pathlib import Path

import chess
import chess.polyglot


PROMOTION_CODES = {
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK: 3,
    chess.QUEEN: 4,
}

STANDARD_CASTLING_TARGETS = {
    (chess.WHITE, chess.G1): chess.H1,
    (chess.WHITE, chess.C1): chess.A1,
    (chess.BLACK, chess.G8): chess.H8,
    (chess.BLACK, chess.C8): chess.A8,
}


def raw_polyglot_move(move: chess.Move) -> int:
    """Pack a Polyglot move into its raw 16-bit representation."""
    promotion = PROMOTION_CODES[move.promotion] if move.promotion else 0
    return move.to_square | (move.from_square << 6) | (promotion << 12)


def polyglot_move(board: chess.Board, move: chess.Move) -> chess.Move:
    """Return the move representation stored in a Polyglot book."""
    if not board.chess960 and board.is_castling(move):
        return chess.Move(move.from_square, STANDARD_CASTLING_TARGETS[(board.turn, move.to_square)])

    return move


def san_tokens(pgn: str) -> list[str]:
    """Split a PGN line from the openings TSV into SAN tokens."""
    cleaned = re.sub(r"\{[^}]*\}", " ", pgn)
    cleaned = re.sub(r"\d+\.(?:\.\.)?", " ", cleaned)
    return [
        token
        for token in cleaned.split()
        if token not in {"*", "1-0", "0-1", "1/2-1/2"}
    ]


def build_entries(tsv_paths: list[Path]) -> Counter[tuple[int, int]]:
    """Build weighted Polyglot entries from lichess openings TSV files."""
    entries: Counter[tuple[int, int]] = Counter()

    for path in tsv_paths:
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                board = chess.Board()
                for token in san_tokens(row["pgn"]):
                    move = board.parse_san(token)
                    key = chess.polyglot.zobrist_hash(board)
                    entries[(key, raw_polyglot_move(polyglot_move(board, move)))] += 1
                    board.push(move)

    return entries


def write_polyglot(entries: Counter[tuple[int, int]], output: Path) -> None:
    """Write weighted entries to a Polyglot book file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        for (key, raw_move), count in sorted(entries.items()):
            weight = min(count, 65535)
            file.write(struct.pack(">QHHI", key, raw_move, weight, 0))


def main() -> None:
    """Build a Polyglot book from an openings TSV directory."""
    parser = argparse.ArgumentParser(description="Build a Polyglot book from lichess-org/chess-openings TSV files.")
    parser.add_argument("tsv_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    tsv_paths = sorted(args.tsv_dir.glob("*.tsv"))
    if not tsv_paths:
        raise SystemExit(f"No TSV files found in {args.tsv_dir}")

    entries = build_entries(tsv_paths)
    write_polyglot(entries, args.output)
    sys.stdout.write(f"Wrote {len(entries)} Polyglot entries to {args.output}\n")


if __name__ == "__main__":
    main()
