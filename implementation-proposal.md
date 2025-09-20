# Návrh realizácie Automa - Python Agent Management Platform

## 1. Technologický stack

### Backend
- **Framework**: FastAPI 0.104+ (asynchrónny, rýchly, automatická OpenAPI dokumentácia)
- **Databáza**: SQLite s SQLAlchemy 2.0 (migrácia na PostgreSQL pri škálovaní)
- **Autentifikácia**: FastAPI-Users s JWT tokenmi
- **Task scheduling**: APScheduler (jednoduchšie ako Celery pre začiatok)
- **Validácia**: Pydantic v2
- **Migrácie**: Alembic
- **Testing**: pytest s async podporou

### Sandboxovanie a bezpečnosť
- **Kontajnerizácia**: Docker containers pre izoláciu skriptov
- **Resource limits**: Docker memory/CPU limits
- **Network isolation**: Vlastné Docker siete
- **File system**: Read-only bind mounts pre skripty

### Frontend
- **Framework**: Vue.js 3 s Composition API
- **UI library**: Vuetify 3 (Material Design)
- **State management**: Pinia
- **HTTP client**: Axios
- **Build tool**: Vite

## 2. Architektúra databázy

### Základné entity

```sql
-- Používatelia a autentifikácia
users (id, email, hashed_password, is_active, is_superuser, created_at)
user_sessions (id, user_id, token, expires_at, created_at)

-- Skripty a agenti
scripts (id, name, description, file_path, created_by, created_at, updated_at)
agents (id, name, description, script_id, config_json, created_by, is_active)

-- Úlohy a plánovanie
jobs (id, agent_id, name, schedule_type, cron_expression, next_run, is_active)
job_executions (id, job_id, started_at, finished_at, status, output, error_log)

-- Audit log
audit_logs (id, user_id, action, resource_type, resource_id, timestamp, details_json)
```

## 3. API štruktúra (FastAPI)

### Autentifikácia endpoints
```
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
```

### Scripts management
```
GET    /api/v1/scripts
POST   /api/v1/scripts
GET    /api/v1/scripts/{id}
PUT    /api/v1/scripts/{id}
DELETE /api/v1/scripts/{id}
POST   /api/v1/scripts/{id}/upload
```

### Agents management
```
GET    /api/v1/agents
POST   /api/v1/agents
GET    /api/v1/agents/{id}
PUT    /api/v1/agents/{id}
DELETE /api/v1/agents/{id}
POST   /api/v1/agents/{id}/start
POST   /api/v1/agents/{id}/stop
GET    /api/v1/agents/{id}/status
GET    /api/v1/agents/{id}/logs
```

### Jobs scheduling
```
GET    /api/v1/jobs
POST   /api/v1/jobs
GET    /api/v1/jobs/{id}
PUT    /api/v1/jobs/{id}
DELETE /api/v1/jobs/{id}
GET    /api/v1/jobs/{id}/executions
```

### Monitoring a audit
```
GET /api/v1/monitoring/system
GET /api/v1/monitoring/agents
GET /api/v1/audit/logs
```

## 4. Adresárová štruktúra

```
automa/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Konfigurácia
│   │   ├── database.py             # DB connection
│   │   ├── models/                 # SQLAlchemy modely
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── script.py
│   │   │   ├── agent.py
│   │   │   └── job.py
│   │   ├── schemas/                # Pydantic schémy
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── script.py
│   │   │   ├── agent.py
│   │   │   └── job.py
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── scripts.py
│   │   │   ├── agents.py
│   │   │   └── jobs.py
│   │   ├── services/               # Business logika
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── script_service.py
│   │   │   ├── agent_service.py
│   │   │   ├── scheduler_service.py
│   │   │   └── sandbox_service.py
│   │   ├── core/                   # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── deps.py
│   │   │   └── audit.py
│   │   └── sandbox/                # Sandboxovanie
│   │       ├── __init__.py
│   │       ├── docker_runner.py
│   │       └── base_sandbox.py
│   ├── scripts/                    # Používateľské skripty
│   ├── data/                       # SQLite DB a logy
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── router/
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.sandbox
│   └── docker-compose.yml
└── README.md
```

## 5. Bezpečnostné opatrenia

### Autentifikácia a autorizácia
- JWT tokeny s refresh mechanizmom
- Hashované heslá (bcrypt)
- Role-based access control (RBAC)
- Session management s expiry

### Sandboxovanie
```python
# Príklad Docker sandbox konfigurácie
SANDBOX_CONFIG = {
    "image": "python:3.13-slim",
    "memory_limit": "256m",
    "cpu_limit": "0.5",
    "network_mode": "none",
    "read_only": True,
    "user": "sandbox:sandbox",
    "timeout": 300
}
```

### Audit trail
- Všetky API calls logované
- User actions tracking
- Script execution logs
- System events monitoring

## 6. Implementačné fázy

### ✅ Fáza 1: Základná infraštruktúra (DOKONČENÁ)
- [x] FastAPI backend setup
- [x] SQLAlchemy modely a migrácie
- [x] Základná autentifikácia
- [x] Vue.js frontend setup
- [x] Docker kontajnerizácia

### ✅ Fáza 2: Core funkcionalita (DOKONČENÁ)
- [x] Script management (upload, edit, delete)
- [x] Základný agent management
- [x] Docker sandbox implementácia
- [x] Job scheduling s APScheduler
- [x] Základné UI komponenty

### ✅ Fáza 3: Pokročilé funkcie (DOKONČENÁ)
- [x] Real-time monitoring
- [x] Advanced scheduling (cron expressions)
- [x] Audit logging
- [x] User management UI
- [x] API dokumentácia

### 🔄 Fáza 4: Bezpečnosť a optimalizácia (ČIASTOČNE)
- [x] Security audit
- [ ] Performance optimization
- [x] Error handling improvement
- [ ] Testing coverage
- [x] Documentation

### 📋 Ďalšie kroky pre produkciu
- [ ] Kompletné testovanie
- [ ] Performance optimalizácia
- [ ] PostgreSQL migrácia
- [ ] Advanced monitoring
- [ ] Backup stratégia
- [ ] CI/CD pipeline

## 7. Konfigurácia a deployment

### Lokálny development
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production deployment
```bash
docker-compose up -d
```

### Environment variables
```env
DATABASE_URL=sqlite:///./data/automa.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SANDBOX_IMAGE=automa-sandbox:latest
```

## 8. Monitoring a maintenance

### Zdravotné kontroly
- API health check endpoints
- Database connection monitoring
- Docker container status
- Disk space monitoring

### Logging
- Štruktúrované JSON logy
- Log rotation (logrotate)
- Error alerting
- Performance metrics

### Backup stratégia
- Automatické DB backupy
- Script files backup
- Configuration backup
- Recovery procedures

## 9. Rozšíriteľnosť

### Plugin systém
- Plugin interface definícia
- Dynamic loading mechanizmus
- Plugin configuration management
- Plugin marketplace (budúcnosť)

### MCP rozhranie
- Model Context Protocol implementácia
- External tool integration
- API gateway pre externí prístup
- Webhook support

### Škálovanie
- Horizontal scaling s load balancer
- Database clustering (PostgreSQL)
- Distributed task queue (Celery)
- Kubernetes deployment

Tento návrh poskytuje solídny základ pre bezpečnú, škálovateľnú platformu na správu Python agentov s dôrazom na bezpečnosť a rozšíriteľnosť.