# Správne príkazy pre Automa

## ✅ Fungujúce príkazy po oprave

### Setup projektu
```bash
# Inštalácia dependencies
uv sync
```

### Spustenie backendu
```bash
# Všetky tieto príkazy fungujú:
uv run main.py                                      # Port 8001
uv run uvicorn backend.app.main:app --reload        # Port 8000
uv run scripts/dev.py backend                       # Port 8000
```

### Development skripty
```bash
uv run scripts/dev.py backend     # Spustenie backendu
uv run scripts/dev.py install     # Inštalácia všetkých deps
uv run scripts/dev.py test        # Spustenie testov
uv run scripts/dev.py lint        # Linting kódu
```

## ❌ Nefungujúce príkazy

```bash
# NEPOUŽÍVAŤ - chybný module path
uv run uvicorn automa.api.app:app --reload
```

## 🔧 Opravené problémy

1. **Chýbajúce dependencies**: Pridané `pydantic-settings`, `aiofiles`
2. **FastAPI-Users API**: Opravený import z `JWTAuthentication` na `JWTStrategy`
3. **Windows encoding**: Odstránené emoji z development skriptov
4. **Module path**: Správny path je `backend.app.main:app`

## 📦 Nainštalované dependencies

- fastapi, uvicorn, sqlalchemy, alembic
- pydantic, pydantic-settings
- fastapi-users, passlib, python-jose
- docker, apscheduler
- aiosqlite, aiofiles
- pytest, ruff, httpx (dev)

## 🎯 API Endpoints

Po spustení servera:
- **API docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health
- **Root**: http://localhost:8000/