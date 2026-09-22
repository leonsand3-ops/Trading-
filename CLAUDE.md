# CLAUDE.md

Beslutsstöd för swing trading i amerikanska aktier. Läs `docs/status.md` (var vi är),
`docs/architecture.md` och
`docs/decisions.md` innan större ändringar.

**Gammal kod:** `backend/`, `frontend/`, `start.bat` och `README.md` hör till ett
tidigare, orelaterat projekt. Använd dem inte, bygg inte vidare på dem och importera
inget från dem. Allt nytt ligger i `src/swing/`, `tests/` och `docs/`.

## Kommandon

```bash
uv sync                      # installera beroenden
uv run pytest                # tester
uv run ruff check .          # lint
uv run ruff format .         # formatering
uv run mypy                  # typkontroll
uv run swing --help          # CLI
```

Kör pytest, ruff och mypy innan en ändring räknas som klar.

## Struktur

```
src/swing/
  data/       leverantörsadapters, point-in-time-lagring, datakvalitet
  features/   indikatorer och features (rena funktioner)
  regime/     marknadsregim
  setups/     en modul per setup, implementerad mot docs/setups/<namn>.md
  risk/       riskmotor och kostnadsmodell
  thesis/     thesis-kontrakt och pelarkontroller
  monitor/    daglig positionsbevakning
  llm/        prompts (versionerade), scheman, klient, evals
  backtest/   event-driven motor på dagsdata
  journal/    signaler, beslut, utfall
  broker/     BrokerAdapter, ManualBroker
tests/        speglar src/swing/
docs/         architecture.md, decisions.md, setups/
```

## Regler som inte får brytas

1. **Ingen look-ahead.** All data som används för ett beslut dag t hämtas via
   as-of-åtkomst som bara exponerar data till och med t. Nya features och setups ska ha
   truncation-test.
2. **Point-in-time.** Varje rad med extern data har `event_time` och `known_at`.
   Data skrivs inte över, nya versioner läggs till.
3. **Instrument identifieras med stabilt ID**, aldrig bara ticker.
4. **Allt i R.** Resultat och risk uttrycks i R (risken från entry till stopp).
5. **AI beslutar inte.** LLM-output är text eller validerade features. Den används
   aldrig direkt som pris, storlek, sannolikhet eller order.
6. **Stopp vidgas aldrig.** Monitor- och exit-logik får bara dra åt stoppet.
7. **Samma kod i backtest och live.** Setup-, feature- och riskkod vet inte om den körs
   i backtest.
8. **Kostnader alltid med.** Backtester utan kostnadsmodell räknas inte som resultat.
9. **Logga alla varianter som backtestas**, inte bara den bästa.

## Konventioner

- Python 3.12, strikt typning, Pydantic för domänobjekt och scheman.
- Indikatorer skrivs själva som rena funktioner, inga stora TA-bibliotek.
- Tester använder små syntetiska dataset med kända svar.
- Ny setup: skriv spec i `docs/setups/` först, implementera sedan mot specen.
- Nya arkitekturbeslut läggs till i `docs/decisions.md`.
- Kod och identifierare på engelska, dokumentation på svenska.
