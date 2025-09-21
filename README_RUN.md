# Automa Launcher - run.sh

Jednoduchý skript pre spustenie Automa aplikácie s prístupom z LAN.

## Použitie

```bash
# Spustenie oboch služieb (backend + frontend)
./run.sh

# Alebo explicitne
./run.sh both

# Spustenie len backendu
./run.sh backend

# Spustenie len frontendu
./run.sh frontend

# Zobrazenie help
./run.sh help
```

## Prístup z LAN

Aplikácia bude dostupná z celej lokálnej siete:

- **Frontend**: http://192.168.1.40:8002
- **Backend**: http://192.168.1.40:8001
- **API Dokumentácia**: http://192.168.1.40:8001/docs

*(IP adresa sa automaticky detekuje)*

## Funkcie skriptu

✅ **Automatická kontrola požiadaviek**
- Overí prítomnosť `uv`, `node`, `npm`
- Zobrazí chybové hlášky s inštrukciami

✅ **Automatické nastavenie**
- Vytvorí potrebné adresáre (`data`, `scripts`)
- Nainštaluje závislosti ak treba
- Vytvorí virtuálne prostredie

✅ **LAN prístup**
- Backend počúva na `0.0.0.0:8001`
- Frontend počúva na `0.0.0.0:8002`
- Automaticky detekuje a zobrazí IP adresu

✅ **Pokročilé funkcie**
- Farebný výstup pre lepšiu čitateľnosť
- Graceful shutdown (Ctrl+C zastaví oba procesy)
- Background spustenie pre režim "both"

## Príklady použitia

### Vývoj na jednom počítači
```bash
./run.sh both
# Prístup: http://localhost:8002
```

### Testovanie z iných zariadení v sieti
```bash
./run.sh both
# Prístup z telefónu/tabletu: http://192.168.1.40:8002
```

### Len backend pre API testovanie
```bash
./run.sh backend
# API: http://192.168.1.40:8001/docs
```

## Zastavenie služieb

- **Režim "both"**: `Ctrl+C` (zastaví oba procesy)
- **Jednotlivé služby**: `Ctrl+C`
- **Background procesy**: `pkill -f uvicorn` alebo `pkill -f "npm run dev"`

## Poznámky

- Skript automaticky detekuje lokálnu IP adresu
- Použije `--reload` pre automatické reštartovanie pri zmenách
- Frontend bude dostupný na inom porte ak je 8002 obsadený
- Backend vždy beží na porte 8001