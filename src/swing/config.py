"""Runtime settings."""

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path("data")


def data_dir() -> Path:
    """Directory of the local data lake, overridable with ``SWING_DATA_DIR``."""
    return Path(os.environ.get("SWING_DATA_DIR", DEFAULT_DATA_DIR))


def read_symbol_file(path: Path) -> list[str]:
    """Symbols from a text file, one per line; ``#`` starts a comment."""
    symbols = []
    for line in path.read_text(encoding="utf-8").splitlines():
        symbol = line.split("#", 1)[0].strip()
        if symbol:
            symbols.append(symbol.upper())
    return symbols
