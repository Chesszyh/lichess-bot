"""Tests for the lichess openings Polyglot book builder."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import chess
import chess.polyglot


def load_builder() -> ModuleType:
    """Load the book builder script as a module."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_lichess_openings_book.py"
    spec = importlib.util.spec_from_file_location("build_lichess_openings_book", script_path)
    assert spec
    assert spec.loader

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_opening_rows(path: Path, rows: list[str]) -> None:
    """Write a minimal lichess-org/chess-openings style TSV file."""
    path.write_text("eco\tname\tpgn\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_write_polyglot__preserves_weights_and_standard_castling_encoding(tmp_path: Path) -> None:
    """Generated books should keep weights and encode standard castling for Polyglot consumers."""
    builder = load_builder()
    tsv_path = tmp_path / "openings.tsv"
    output_path = tmp_path / "book.bin"
    write_opening_rows(tsv_path, [
        "C60\tRuy Lopez\t1. e4 e5 2. Nf3 Nc6 3. Bb5 a6",
        "C60\tRuy Lopez\t1. e4 e5 2. Nf3 Nc6 3. Bb5 a6",
        "C80\tRuy Lopez\t1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O",
    ])

    builder.write_polyglot(builder.build_entries([tsv_path]), output_path)

    board = chess.Board()
    with chess.polyglot.open_reader(output_path) as reader:
        opening_entry = next(reader.find_all(board))
        assert opening_entry.move == chess.Move.from_uci("e2e4")
        assert opening_entry.weight == 3

        for san in ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6"]:
            board.push_san(san)

        castling_entry = next(reader.find_all(board))
        assert castling_entry.move == chess.Move.from_uci("e1g1")
        assert castling_entry.raw_move == builder.raw_polyglot_move(chess.Move.from_uci("e1h1"))
