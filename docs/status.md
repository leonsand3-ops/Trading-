# Status

Läs den här filen först i varje ny session. Uppdatera den när något är klart.

## Senast uppdaterad: 2026-09-22

### Klart
- **Fas 0:** arkitektur (`docs/architecture.md`), beslutslogg (`docs/decisions.md`),
  `CLAUDE.md`, Python-skelett, tester, lint, typkontroll, CI.
- **Fas 1 (kod):** point-in-time-datalager i `src/swing/data/`: append-only
  Parquet-lagring, stabila instrument-ID:n, as-of-åtkomst med truncation- och
  future-poisoning-tester, Yahoo- och CSV-adaptrar, datakvalitetskontroller, CLI
  (`swing data update | check | show`), stegvis uppdatering, sex timmars väntetid
  efter stängning innan en dag sparas.
- Användaren har kört allt på sin Windows-dator: 55 symboler, 221 163 rader,
  2010-01-04 till 2026-09-22.

### Pågår
- **Verifiera fas 1 på användarens dator.** Första `data check` gav 4 fel
  (`ohlc_inconsistent` för DIA, GS, UNH, DIS på 2026-09-22), eftersom datan hämtades
  direkt efter stängning. Användaren kör efter 04:00 svensk tid:
  `cd Trading-`, `git pull`, `uv run swing data update`, `uv run swing data check`.
  Förväntat: 0 error. Kvarvarande varningar är kända och godkända: large_move för
  AMD 2016-04-22, SMCI 2018-10-04 och NFLX 2013-01-24 (verkliga händelser);
  zero_volume för XLRE 2015 och AMD 2015-01-02; stale_close för SMCI 2017-02-14.

### Nästa steg
1. Bekräfta 0 error ovan. Då är fas 1 klar.
2. **Fas 2:** indikatorer (rena funktioner med truncation-tester), marknadsregim,
   spec + implementation av 2–3 setups (`docs/setups/`), event-driven backtestmotor
   med kostnadsmodell.
3. Före riktiga backtestresultat: användaren väljer betald datakälla utan
   survivorship bias (rekommendation Norgate, fungerar på Windows). Databudget ej
   bestämd.

### Att känna till om användaren
- Kör Windows 11 och PowerShell, ny på git och kommandoraden. Ge exakta kommandon,
  ett i taget, och påminn om `cd Trading-`.
- Svensktalande. ISK hos Nordnet, positioner 2 000–15 000 kr, amerikanska aktier.
- Den gamla koden (`backend/`, `frontend/`, `start.bat`, `README.md`) ska ligga kvar
  orörd.
