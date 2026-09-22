# Kom igång på Windows

## Engångsinstallation

1. Installera Git: <https://git-scm.com/download/win>
2. Installera uv (hanterar Python och paket). Öppna PowerShell och kör:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Stäng och öppna PowerShell igen efteråt.
3. Hämta projektet:

   ```powershell
   git clone https://github.com/leonsand3-ops/Trading-.git
   cd Trading-
   git checkout claude/eloquent-davinci-er9w0a
   ```

4. Installera beroenden (uv hämtar rätt Python-version själv):

   ```powershell
   uv sync --extra yahoo
   ```

## Hämta och kontrollera data

```powershell
uv run swing data update                 # hela utvecklingsuniversumet sedan 2010
uv run swing data update --symbols NVDA  # en enskild aktie
uv run swing data check                  # datakvalitetsrapport
uv run swing data show NVDA              # senaste barerna
uv run swing data show NVDA --as-of 2024-03-01   # så som datan var känd det datumet
```

Datan sparas i mappen `data\` i projektet. Den checkas inte in i git.
Byt plats med miljövariabeln `SWING_DATA_DIR`.

Kör `swing data update` igen när du vill ha ny data. Inget skrivs över; varje körning
sparas som en ny version.

## Egna CSV-filer

Lägg filer som `NVDA.csv` med kolumnerna `date,open,high,low,close,volume` i en mapp:

```powershell
uv run swing data update --source csv --csv-dir C:\sökväg\till\mappen --symbols NVDA
```
