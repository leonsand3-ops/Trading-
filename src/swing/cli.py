"""Command line entry point."""

from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated

import typer

from swing import __version__
from swing.config import data_dir, read_symbol_file
from swing.data.asof import BarHistory
from swing.data.calendar import latest_final_session
from swing.data.ingest import incremental_starts, ingest_bars
from swing.data.instruments import InstrumentRegistry
from swing.data.providers import BarProvider, CsvProvider, YahooProvider
from swing.data.quality import Severity, check_bars
from swing.data.store import DataStore

app = typer.Typer(no_args_is_help=True, help="Beslutsstöd för swing trading.")
data_app = typer.Typer(no_args_is_help=True, help="Hämta och kontrollera marknadsdata.")
app.add_typer(data_app, name="data")

DEFAULT_UNIVERSE = Path("config/universe_dev.txt")
DEFAULT_START = date(2010, 1, 1)


@app.callback()
def main() -> None:
    """Swing trading decision support."""


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(__version__)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


@data_app.command("update")
def data_update(
    symbols: Annotated[
        str | None, typer.Option(help="Kommaseparerade symboler, t.ex. AAPL,MSFT.")
    ] = None,
    universe: Annotated[Path, typer.Option(help="Fil med en symbol per rad.")] = DEFAULT_UNIVERSE,
    start: Annotated[
        str | None,
        typer.Option(
            help="Startdatum ÅÅÅÅ-MM-DD för alla symboler. Utan: bara nya dagar, "
            f"eller från {DEFAULT_START} för symboler som saknas."
        ),
    ] = None,
    end: Annotated[str | None, typer.Option(help="Slutdatum, standard idag.")] = None,
    source: Annotated[str, typer.Option(help="yahoo eller csv.")] = "yahoo",
    csv_dir: Annotated[Path | None, typer.Option(help="Katalog med <SYMBOL>.csv.")] = None,
) -> None:
    """Hämta dagsdata och spara som en ny version."""
    provider: BarProvider
    if source == "yahoo":
        provider = YahooProvider()
    elif source == "csv":
        if csv_dir is None:
            raise typer.BadParameter("--csv-dir krävs med --source csv")
        provider = CsvProvider(csv_dir)
    else:
        raise typer.BadParameter(f"okänd källa: {source}")

    symbol_list = (
        [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if symbols
        else read_symbol_file(universe)
    )
    end_date = _parse_date(end) if end else date.today()
    store = DataStore(data_dir())
    typer.echo(f"Hämtar {len(symbol_list)} symboler från {provider.source}...")

    def progress(position: int, total: int, symbol: str) -> None:
        typer.echo(f"  [{position}/{total}] {symbol}")

    now = datetime.now(UTC)
    starts = (
        _parse_date(start)
        if start
        else incremental_starts(store, provider.source, symbol_list, DEFAULT_START)
    )
    result = ingest_bars(
        provider,
        symbol_list,
        starts,
        end_date,
        store,
        now,
        on_symbol=progress,
    )
    total = sum(result.rows_written.values())
    typer.echo(f"Sparade {total} rader för {len(result.rows_written)} symboler i {store.root}")
    if result.last_date:
        typer.echo(f"Senaste börsdag som sparades: {max(result.last_date.values())}")
        expected = latest_final_session(now)
        behind = [s for s, last in result.last_date.items() if last < expected]
        if behind:
            typer.echo(
                f"OBS: {len(behind)} av {len(result.last_date)} symboler saknar {expected}. "
                f"{provider.source} har inte publicerat dagen än, eller så var det helgdag "
                "i USA. Kör uppdateringen igen senare."
            )
    for symbol, reason in result.failures.items():
        typer.echo(f"  MISSLYCKADES {symbol}: {reason}", err=True)
    if result.failures and not result.rows_written:
        raise typer.Exit(1)


@data_app.command("check")
def data_check(
    show: Annotated[int, typer.Option(help="Antal problem att lista.")] = 20,
) -> None:
    """Kör datakvalitetskontroller på lagrad data."""
    store = DataStore(data_dir())
    bars = store.latest_bars()
    if bars.is_empty():
        typer.echo("Ingen data. Kör `swing data update` först.")
        raise typer.Exit(1)
    symbols = InstrumentRegistry(store).symbols()
    issues = check_bars(bars)
    n_instruments = bars.get_column("instrument_id").n_unique()
    dates = bars.get_column("date")
    first, last = str(dates.min()), str(dates.max())
    typer.echo(f"{bars.height} rader, {n_instruments} instrument, {first} till {last}")
    counts = Counter((i.severity, i.check) for i in issues)
    if not counts:
        typer.echo("Inga problem hittades.")
        return
    for (severity, check), n in sorted(counts.items()):
        typer.echo(f"  {severity.value:<7} {check:<26} {n}")
    ordered = sorted(issues, key=lambda i: (i.severity != Severity.ERROR, i.check))
    typer.echo(f"\nFörsta {min(show, len(issues))} problemen:")
    for issue in ordered[:show]:
        symbol = symbols.get(issue.instrument_id, issue.instrument_id)
        typer.echo(
            f"  {issue.severity.value:<7} {symbol:<6} {issue.date} {issue.check}: {issue.detail}"
        )
    if any(i.severity == Severity.ERROR for i in issues):
        raise typer.Exit(1)


@data_app.command("show")
def data_show(
    symbol: str,
    as_of: Annotated[
        str | None, typer.Option(help="Visa data som den var känd vid stängning detta datum.")
    ] = None,
    tail: Annotated[int, typer.Option(help="Antal rader.")] = 10,
) -> None:
    """Visa de senaste barerna för en symbol."""
    store = DataStore(data_dir())
    registry = InstrumentRegistry(store)
    ids = [iid for iid, s in registry.symbols().items() if s == symbol.upper()]
    if not ids:
        typer.echo(f"Okänd symbol: {symbol}")
        raise typer.Exit(1)
    history = BarHistory.load(store)
    view = history.at_close(_parse_date(as_of) if as_of else date.today())
    for instrument_id in ids:
        df = view.bars(instrument_id, lookback=tail)
        typer.echo(df.select("date", "open", "high", "low", "close", "volume", "source"))
