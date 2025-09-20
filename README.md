# Automa - Python Agent Management Platform

**Status: ✅ Fully Functional**

Webová aplikácia na správu Python aplikácií a agentov pre automatizáciu rutinných úloh.

## Aktuálny stav projektu

Platforma je plne funkčná s nasledujúcimi komponentami:
- ✅ **Backend API**: FastAPI server beží na porte 8001
- ✅ **Frontend UI**: Vue.js 3 + Vuetify beží na porte 8002
- ✅ **Autentifikácia**: JWT tokeny s argon2 hashovaním (opravené)
- ✅ **Databáza**: SQLite s inicializovanými tabuľkami
- ✅ **Docker**: Pripravená konfigurácia pre sandboxovanie
- ✅ **Development tools**: uv package manager plne nakonfigurovaný

## Funkcionalita

- **Správa skriptov**: Upload, editácia a spúšťanie Python skriptov
- **Agent management**: Vytváranie a riadenie automatizačných agentov
- **Plánovanie úloh**: Cron-based scheduling a ad-hoc spúšťanie
- **Bezpečné sandboxovanie**: Docker izolácia pre bezpečné spúšťanie skriptov
- **Monitoring a audit**: Kompletné logovanie a sledovanie aktivít
- **Multi-user podpora**: Autentifikácia a role-based prístup

## Technológie

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue.js 3 + Vuetify + Pinia
- **Dependency Management**: uv (modern Python package manager)
- **Sandboxovanie**: Docker containers
- **Autentifikácia**: JWT tokens
- **Plánovanie**: APScheduler

## Štruktúra projektu

```
automa/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── models/    # SQLAlchemy modely
│   │   ├── schemas/   # Pydantic schémy
│   │   ├── api/       # API routes
│   │   ├── services/  # Business logika
│   │   └── core/      # Core utilities
│   ├── scripts/       # Používateľské skripty
│   └── data/          # SQLite databáza
├── frontend/          # Vue.js frontend
├── docker/            # Docker konfigurácie
├── scripts/           # Development skripty
├── pyproject.toml     # uv konfigurácia
└── docker-compose.yml
```

## Rýchly štart

### Inštalácia uv

Ak nemáte nainštalované uv:
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Lokálny development

1. **Setup celého projektu**:
```bash
# Vytvorenie potrebných adresárov
mkdir -p data scripts

# Inštalácia Python dependencies
uv sync

# Inštalácia frontend dependencies
cd frontend && npm install && cd ..
```

2. **Spustenie aplikácie**:
```bash
# Backend (port 8001)
uv run main.py                    # Hlavný entry point
uv run scripts/dev.py backend     # Development script
uv run uvicorn backend.app.main:app --reload --port 8001

# Frontend (port 8002)
uv run scripts/dev.py frontend    # Development script
# alebo
cd frontend && npm run dev
```

3. **Ďalšie užitočné príkazy**:
```bash
uv run scripts/dev.py install     # Inštalácia všetkých dependencies
uv run scripts/dev.py test        # Spustenie testov
uv run scripts/dev.py lint        # Linting kódu
```

### Docker deployment

```bash
# Build a spustenie všetkých služieb
docker-compose up -d

# Build sandbox image
docker-compose build sandbox-builder
```

## Konfigurácia

Skopírujte `.env.example` do `.env` a upravte podľa potreby:

```bash
cp .env.example .env
```

Kľúčové nastavenia:
- `SECRET_KEY`: JWT secret (zmeňte v produkcii!)
- `DATABASE_URL`: SQLite databáza
- `SANDBOX_IMAGE`: Docker image pre sandboxovanie
- `CORS_ORIGINS`: Povolené origins pre CORS

## API Dokumentácia

Po spustení aplikácie je dostupná na:
- **Backend Swagger UI**: http://localhost:8001/docs
- **Backend OpenAPI JSON**: http://localhost:8001/openapi.json
- **Frontend**: http://localhost:8002/

## Development Commands

### Použitie uv

```bash
# Inštalácia dependencies
uv sync

# Pridanie novej dependency
uv add fastapi

# Pridanie dev dependency
uv add --dev pytest

# Spustenie skriptu
uv run main.py

# Spustenie v izolovanom prostredí
uv run --isolated python script.py
```

### Testovanie a kvalita kódu

```bash
# Backend testy
uv run pytest backend/tests/

# Linting
uv run ruff check backend/
uv run ruff format backend/

# Type checking
uv run mypy backend/

# Frontend testy
cd frontend && npm run test
```

## Bezpečnosť

- **Docker sandboxovanie**: Všetky skripty bežia v izolovaných kontajneroch
- **Resource limits**: Memory a CPU obmedzenia
- **Network izolácia**: Skripty nemajú prístup k sieti
- **Audit logging**: Všetky akcie sú logované
- **JWT autentifikácia**: Bezpečný prístup k API

## Vývoj

### Pridanie nových API endpoints

1. Vytvorte endpoint v `backend/app/api/`
2. Pridajte schémy do `backend/app/schemas/`
3. Implementujte business logiku v `backend/app/services/`
4. Registrujte router v `backend/app/main.py`

### Pridanie nových Vue komponentov

1. Vytvorte komponent v `frontend/src/components/`
2. Pridajte route do `frontend/src/router/`
3. Aktualizujte navigáciu v `frontend/src/App.vue`

### Pridanie Python dependencies

```bash
# Produkčná dependency
uv add package-name

# Development dependency
uv add --dev package-name

# Aktualizácia všetkých dependencies
uv lock --upgrade
```

## Nasadenie

### Produkčné prostredie

1. Nastavte environment variables
2. Zmeňte `SECRET_KEY` na bezpečnú hodnotu
3. Použite PostgreSQL namiesto SQLite (voliteľné)
4. Spustite cez `docker-compose`

### Backup

```bash
# Backup SQLite databázy
cp backend/data/automa.db backup/automa_$(date +%Y%m%d).db

# Backup skriptov
tar -czf backup/scripts_$(date +%Y%m%d).tar.gz backend/scripts/
```

## Výhody uv

- **Rýchlosť**: 10-100x rýchlejšie než pip
- **Deterministické buildy**: Automatické lock súbory
- **Jednoduchosť**: Jeden nástroj pre všetko (virtual envs, dependencies, scripts)
- **Kompatibilita**: Plne kompatibilné s pip a pyproject.toml
- **Bezpečnosť**: Lepšie dependency resolution

## Známe problémy a riešenia

### Autentifikácia
- **Problém**: Login endpoint vracal 500 error
- **Riešenie**: Opravená `on_after_login` metóda v UserManager a pridaná podpora argon2

### Virtual Environment
- **Problém**: Path issues na Windows
- **Riešenie**: Recreate venv pomocou `rm -rf .venv && uv venv && uv sync`

## Ďalší vývoj

- [x] ~~Oprava autentifikácie~~ ✅
- [x] ~~Konfigurácia uv package managera~~ ✅
- [ ] PostgreSQL podpora
- [ ] Advanced scheduling (cron expressions)
- [ ] Real-time monitoring dashboard
- [ ] Plugin systém
- [ ] MCP rozhranie
- [ ] Kubernetes deployment
- [ ] 2FA autentifikácia

## Podpora

Pre otázky a hlásenie chýb vytvorte issue v repository alebo kontaktujte vývojársky tím.