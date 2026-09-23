# Status

Läs den här filen först i varje ny session. Uppdatera den när något är klart.

## Senast uppdaterad: 2026-09-23

### Klart
- **Fas 0:** arkitektur (`docs/architecture.md`), beslutslogg (`docs/decisions.md`),
  `CLAUDE.md`, Python-skelett, tester, lint, typkontroll, CI.
- **Fas 1 (kod):** point-in-time-datalager i `src/swing/data/`: append-only
  Parquet-lagring, stabila instrument-ID:n, as-of-åtkomst med truncation- och
  future-poisoning-tester, Yahoo- och CSV-adaptrar, datakvalitetskontroller, CLI
  (`swing data update | check | show`), stegvis uppdatering, och regeln att en
  dagsbar räknas först när datumet slagit om i New York (`FINAL_BAR`).
- **Fas 1 verifierad på användarens dator 2026-09-23:** 55 instrument, 221 108 rader,
  2010-01-04 till 2026-09-21, inga error-rader. Kända och godkända varningar:
  large_move för AMD 2016-04-22, SMCI 2018-10-04 och NFLX 2013-01-24 (verkliga
  händelser); zero_volume för XLRE 2015 och AMD 2015-01-02; stale_close för SMCI
  2017-02-14. Yahoo hade då inte publicerat 2026-09-22 (OBS-raden visade det).

### Nästa steg: fas 2
1. Indikatorer som rena funktioner med truncation-tester: SMA/EMA, ATR, relativ
   styrka mot SPY, volym mot snitt, 52-veckors högsta, avstånd i ATR.
2. Marknadsregim: SPY-trend, breadth (andel av universumet över MA50), volatilitet
   → 3–4 lägen.
3. Specar i `docs/setups/` för base breakout och pullback i upptrend. Post-earnings
   väntar tills vi har earnings-data.
4. Kostnadsmodell: courtage, valutaväxling, spread/slippage. Användarens
   courtageklass hos Nordnet behövs (ej känd än).
5. Event-driven backtestmotor på dagsdata med rapport i R.
6. Körs på Yahoo-data för att se att allt fungerar. Resultaten räknas inte som bevis
   förrän vi har survivorship-fri data; användaren väljer källa (rekommendation
   Norgate) innan dess. Databudget ej bestämd.

### Att känna till om användaren
- Kör Windows 11 och PowerShell, ny på git och kommandoraden. Ge exakta kommandon,
  ett i taget, och påminn om `cd Trading-`.
- Svensktalande. ISK hos Nordnet, positioner 2 000–15 000 kr, amerikanska aktier.
- Den gamla koden (`backend/`, `frontend/`, `start.bat`, `README.md`) ska ligga kvar
  orörd.
