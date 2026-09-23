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

Kör `swing data update` igen när du vill ha ny data. Den hämtar bara de senaste dagarna
för symboler som redan finns (med tio dagars överlapp, så att Yahoos korrigeringar
kommer med). Inget skrivs över; varje körning sparas som en ny version.

En börsdag sparas först när det har blivit nytt datum i New York, dvs. från ca 06:00
svensk tid dagen efter (05:00 några veckor per år när sommartiden skiljer). Samma kväll
visar Yahoo en preliminär dagsbar som inte går att lita på. Har Yahoo inte publicerat
gårdagen ännu skriver `data update` ut en rad som börjar med `OBS:`. Kör då igen senare.

Vill du ladda ner allt på nytt: `uv run swing data update --start 2010-01-01`.

## Egna CSV-filer

Lägg filer som `NVDA.csv` med kolumnerna `date,open,high,low,close,volume` i en mapp:

```powershell
uv run swing data update --source csv --csv-dir C:\sökväg\till\mappen --symbols NVDA
```
