from datetime import UTC, datetime

from swing.data.instruments import InstrumentRegistry
from swing.data.store import DataStore

NOW = datetime(2024, 1, 1, tzinfo=UTC)


def test_resolve_is_stable_across_reloads_and_case_insensitive(store: DataStore) -> None:
    first = InstrumentRegistry(store).resolve("yahoo", "aapl", NOW)
    again = InstrumentRegistry(store).resolve("yahoo", "AAPL", NOW)
    assert first == again
    assert first.startswith("ins_")


def test_same_symbol_from_different_sources_gets_different_ids(store: DataStore) -> None:
    registry = InstrumentRegistry(store)
    assert registry.resolve("yahoo", "AAPL", NOW) != registry.resolve("csv", "AAPL", NOW)
