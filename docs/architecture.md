# Arkitektur

Beslutsstöd för swing trading i amerikanska aktier. Systemet hittar setups, räknar
risk, förklarar och granskar caset, och följer positionen efter köp. Ordrar läggs
manuellt i Nordnet.

## Grundprinciper

1. **Bevisbarhet styr arkitekturen.** Det som hittar trades är deterministiska regler
   som går att backtesta. En LLM går inte att backtesta ärligt (den har tränats på vad
   som hände sedan), så AI ligger som ett lager ovanpå och utvärderas framåt i tiden.
2. **Få setups, djupt förstådda.** 2–4 setups med skrivna specifikationer i
   `docs/setups/`.
3. **Allt räknas i R.** 1R = risken från entry till stopp. Resultat, storlek och
   jämförelser uttrycks i R.
4. **Thesis är ett kontrakt.** Varje del av thesis är ett villkor som kod kan kontrollera.
5. **AI förklarar och granskar, beslutar aldrig.** AI-output är features eller text,
   aldrig priser, storlekar eller ordrar.
6. **Allt loggas, varje lager mäts.** Alla signaler sparas, även de som inte tas eller
   blockeras. Ett lager som inte tillför något tas bort.
7. **Samma kod i backtest och live.** Bara datakälla och klocka skiljer.

## Flöde

```
DATA (point-in-time, append-only)
  priser/volym · corporate actions · earnings · filings/nyheter
  indexmedlemskap inkl. avnoterade · VIX/makro · sektorer
        │
 [1] Universe-filter (likviditet, pris, spread)                    kod
 [2] Features (RS, trend, ATR, volym, nivåer, "priced in"-mått)      kod
 [3] Regime (indextrend, breadth, volatilitet) → 3–4 lägen           kod
 [4] Setup-detektorer → kandidat + plan (entry, stopp, target, hålltid)  kod
 [5] Event-lager: nyheter/8-K → strukturerade events                 AI (smalt)
 [6] Riskmotor → APPROVE / REDUCE / BLOCK + storlek + skäl           kod, veto
 [7] Dossier: thesis-kontrakt + bull/bear + pre-mortem               AI, grundad i fakta
 [8] Red team: oberoende granskning → felscenarier, kill criteria    AI
 [9] Användaren beslutar → manuell order i Nordnet → registrerar fill
[10] Monitor: thesis-pelare + stopp-logik varje dag                  kod
     AI läser nya nyheter mot thesis → flagga, aldrig auto-exit
[11] Journal & utvärdering: attribution per lager                    kod
```

### Daglig rytm (svensk tid, USA öppnar 15:30)

- **Natt/morgon:** EOD-data → scan → risk → dossiers → rapport + notis.
- **Före öppning:** nyheter, gaps, dagens earnings; planer som inte gäller stryks.
- **Under dagen:** bara alerts för positioner.
- **Helg:** veckorapport.

## Entry

- Setupen sätter nivåerna strukturellt: pivot/entry-zon, stopp under base low eller
  swing low, target från measured move eller nästa motstånd.
- Krav: R:R ≥ 2 till första target, stoppavstånd ~1–3 ATR, regimen tillåter setupen,
  ingen earnings inom hålltiden (annars gäller earnings-policyn), tillräcklig likviditet,
  kostnader under gräns (se `docs/decisions.md`).
- Planen skapas kvällen före med villkor, t.ex. "köp över pivot, hoppa över om
  öppningen ligger > 0,5 ATR över pivot, gäller 3 dagar". Stoppet läggs direkt efter köp.
- Backtest: signal vid stängning dag t, entry dag t+1 enligt reglerna.

## Thesis-kontrakt och exit

```yaml
setup: base_breakout
plan: {entry_zone: [101.2, 103.0], stop: 96.8, target: [112, 116], hold: "5-10d"}
pillars:
  - {id: trend,        kind: core,    check: "close > ema20"}
  - {id: catalyst,     kind: core,    check: "no negative event, materiality>=high, since entry"}
  - {id: rel_strength, kind: support, check: "rs_rank_63d >= 70"}
  - {id: sector,       kind: support, check: "sector_etf close > sma50"}
  - {id: regime,       kind: context, check: "regime != risk_off"}
hard_stop: 96.8
time_stop: "< +0.5R efter 7 handelsdagar → exit eller tighten"
earnings_policy: "exit före rapport om vinst < 1.5R, annars halvera"
upgrade_rule: "vid >= +2R och veckotrend intakt → trailing på 10-veckors MA"
```

Status räknas ut av kod varje dag:

| Status | Villkor | Rekommendation |
|---|---|---|
| INTACT | alla pelare håller | HOLD, stoppet följer trailing-regeln |
| WEAKENING | en support-pelare brister | TIGHTEN eller TRIM, med skäl |
| INVALIDATED | en core-pelare brister eller hårda stoppet nås | EXIT |

**Asymmetriregeln:** ny information får bara dra åt stoppet, aldrig vidga det.
Inget fast procentmål: trailing-stoppet låter vinnare löpa, och upgrade-regeln
flyttar en swing trade till en längre trailing när caset växer. Vilken exit-variant
som används avgörs av backtest per setup.

## Riskmotor

Ren funktion: `evaluate(plan, portfolio, market, rules) → RiskDecision`.
Reglerna ligger i versionerad konfiguration; varje regel är en egen testad funktion.
Startvärden (ska testas):

| Nivå | Regler |
|---|---|
| Trade | risk 0,5–1 % av kapitalet; antal = risk / (entry − stopp); max andel av kapitalet per position; max andel av ADV; gap-justerad risk när earnings ligger i fönstret |
| Portfölj | total öppen risk ≤ 4–6 %; max N positioner; max 2 per sektor; 60d-korrelation > 0,7 räknas som en bet |
| Marknad | storlek skalas med regime: risk-on 1,0, choppy 0,5, risk-off inga nya longs |
| Konto | −8 % från topp halverar risken; −15 % stoppar nya trades |
| Kostnad | BLOCK om courtage + valutaväxling + spread > gräns i andel av R |

BLOCK kan bara köras över med loggad motivering, och overrides följs upp.

## AI-lagret

LLM används som funktion: strukturerad input, strukturerad output (JSON-schema), och
varje körning loggas med modell, promptversion och input-hash.

| Roll | Input → output | Utvärdering |
|---|---|---|
| Extraktor | nyhet/8-K → event `{typ, riktning, väsentlighet, tidsstämpel, källa}` | golden set märkt för hand |
| Dossier | beräknade fakta med id → thesis, bull/bear, pre-mortem; varje påstående refererar ett fakta-id, kod kontrollerar att siffror finns i underlaget | framåt, shadow mode |
| Red team | samma fakta men inte bull-texten → felscenarier, kill criteria | framåt |
| Monitor-läsare | ny nyhet + thesis-kontrakt → påverkas pelare X? | flagga till användaren |

Ingen agentloop i den dagliga pipelinen. En research-agent som startas vid behov kan
komma senare.

## Backtesting

- Point-in-time överallt: universum inklusive avnoterade, historiskt indexmedlemskap,
  fundamenta enligt publiceringsdatum, earnings-datum som de var kända, nyheter med
  publiceringstid.
- Split-justerade priser för signaler, utdelningar separat; justerade och ojusterade
  nivåer blandas aldrig.
- Event-driven motor på dagsdata. All dataåtkomst via en `AsOfView` som bara
  exponerar data till och med dag t. Stopp mot dagens low, gap genom stopp fylls på
  öppningen, slippage modelleras.
- Portföljsimulering med samma riskmotor som live.
- Läckagetester i CI: *truncation test* (feature för dag t identisk oavsett om
  historiken efter t finns) och *future poisoning* (nonsens efter t ändrar inga
  signaler till och med t).
- Varje körning sparar konfiguration, git sha och datasnapshot.
- LLM-komponenter backtestas inte.

## Hur edge bevisas

1. Hypotes och spec före test.
2. Mått i R: expectancy, win rate, snittvinst/-förlust, fördelning, antal trades.
3. Baselines: slumpade entries med samma exits, setup utan filter, buy & hold.
4. Robusthet: bootstrap-intervall, ≥ ~100 trades per setup, parameterplatå,
   stabilitet per år och regime, dubbla kostnader.
5. De senaste ~2 åren låses som out-of-sample och används en gång.
6. Alla testade varianter loggas och resultat justeras för antalet försök.
7. 2–3 månader paper trading framåt.
8. Attribution: alla setups vs AI-godkända vs AI-avvisade; tagna vs ej tagna.

## Data

| Behov | Källa |
|---|---|
| EOD-historik utan survivorship bias | Norgate Data (kräver Windows-app) eller Sharadar |
| Löpande data | Massive (f.d. Polygon.io) eller Alpaca |
| Nyheter | Massive/Benzinga, Alpaca news eller Finnhub, plus SEC EDGAR |
| Earnings | Finnhub eller FMP |
| Makro | FRED, VIX |

Alla leverantörer ligger bakom adapter-gränssnitt och rådata sparas. yfinance används
bara för prototyper. Broker: `BrokerAdapter` med `ManualBroker` (användaren registrerar
fills); Nordnets externa API är inte öppet för privatkunder på ett praktiskt sätt.

## Lagring

- **Marknadsdata:** Parquet + DuckDB.
- **Applikationstillstånd:** PostgreSQL (SQLite för att komma igång), via SQLAlchemy.
- Append-only och bitemporalt (`event_time` + `known_at`), stabila instrument-ID:n.

Kärntabeller: `instruments`, `bars_daily`, `corporate_actions`, `earnings_events`,
`news_items`, `news_events`, `regime_snapshots`, `signals`, `trade_plans`,
`risk_decisions`, `theses`, `thesis_checks`, `llm_runs`, `fills`, `positions`,
`position_reviews`, `journal_entries`, `backtest_runs`.

## Tech stack

Python 3.12, uv, ruff, mypy, pytest + hypothesis, Polars/NumPy, Pydantic v2,
SQLAlchemy 2 + Alembic, DuckDB, FastAPI, anthropic SDK. Frontend: React + TypeScript +
Vite, TanStack Query, Tailwind + shadcn/ui, TradingView Lightweight Charts.
Notiser via Telegram eller ntfy. Indikatorer skrivs själva. Ingen Celery, Kafka eller
mikrotjänster.

## Faser

| Fas | Innehåll | Klart när |
|---|---|---|
| 0 | Beslut, skelett, CLAUDE.md, CI | tester och lint körs automatiskt |
| 1 | Datalager: point-in-time, survivorship-fritt, kvalitetskontroller | kvalitetsrapport för datan |
| 2 | Features, regime, 2–3 setups, backtestmotor, läckagetester | forskningsrapport per setup. **Gate: fortsätt bara om minst en setup har robust positiv expectancy efter kostnader** |
| 3 | Scanner, riskmotor, trade plans, journal, daglig rapport och notis | paper trading startar |
| 4 | Position monitor | positioner följs automatiskt |
| 5 | AI-lagret i shadow mode | golden set och loggad utvärdering |
| 6 | Dashboard | |
| 7 | Attribution, meta-labeling | |
| 8 | (Kanske) broker-integration | |

## Inte i första versionen

Agentdebatter, realtid/intradag, ML-prisprediktion, automatiska ordrar, fler än 3–4
setups, sociala medier och options flow, vektordatabas/RAG, mikrotjänster, Norden,
avancerad dashboard innan edge är bevisad.
