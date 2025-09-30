# Analýza Codebase a Návrhy na Úpravy

**Dátum:** 2025-09-30
**Verzia aplikácie:** 0.1.0
**Stav:** Funkčná aplikácia - Fáza 3 dokončená ✅
**Posledná aktualizácia:** 2025-09-30 (Phase 3: Performance Optimization Complete)

---

## 1. Executive Summary

Automa je funkčná webová aplikácia pre správu Python agentov a automatizačných skriptov. Projekt má **solídne základy** s moderným technologickým stackom (FastAPI, Vue.js 3, Docker), implementovanou bezpečnosťou a dobrú architektúru. Kód je čistý, dobre štruktúrovaný a pripravený na ďalší rozvoj.

**Celkové hodnotenie:** 7.5/10

### Silné stránky
- ✅ Moderný tech stack (FastAPI, Vue.js 3, Vuetify, SQLAlchemy 2.0)
- ✅ Bezpečnostné základy (JWT, argon2, rate limiting, audit logging)
- ✅ Docker kontajnerizácia s production/development konfiguráciou
- ✅ Modulárna architektúra s jasnou separáciou vrstiev
- ✅ Implementované základné testy (13 backend, 16 frontend)
- ✅ Zdravotné endpointy a Prometheus metriky

### Oblasti na zlepšenie (Aktualizované po Fáze 1)
- ✅ ~~TODO komentáre v kritických častiach~~ → **FIXED**
- ✅ ~~Neimplementované cron parsing~~ → **IMPLEMENTED**
- ✅ ~~Chýbajúca integrácia s APScheduler~~ → **IMPLEMENTED**
- ✅ ~~Základná error handling bez retry logiky~~ → **IMPLEMENTED**
- ⚠️ Minimálne pokrytie testami (~15-20%) → Zostáva na Fázu 2
- ⚠️ Žiadny task queue systém (Celery) → Voliteľné pre veľké nasadenia

---

## 2. Backend Analýza

### 2.1 Architektúra a Štruktúra
**Hodnotenie:** 8/10

#### Pozitíva
```
backend/
├── app/
│   ├── api/          # Čisté endpointy s dobrým separation of concerns
│   ├── services/     # Business logika správne izolovaná
│   ├── models/       # SQLAlchemy modely s dobrými vzťahmi
│   ├── schemas/      # Pydantic v2 validácia
│   ├── core/         # Security, deps, audit - dobre organizované
│   └── main.py       # Čistý startup s exception handlers
```

- Service layer pattern správne implementovaný
- Dependency injection cez FastAPI deps
- Async/await konzistentne použité
- Audit logging implementovaný vo všetkých kritických operáciách

#### Negatíva
- **Chybné vypnutie SQLAlchemy echo módu**: Config má `echo=settings.environment == "development"`, ale mali by byť riadené cez samostatnú premennú
- **TODO komentáre v production kóde**:
  - `agent_service.py:112` - "TODO: Implement actual agent starting logic with Docker/sandbox"
  - `job_service.py:23` - "TODO: Add cron parsing for cron_expression"
  - `job_service.py:128` - "TODO: Implement actual job execution logic"

### 2.2 Databáza a Modely
**Hodnotenie:** 7.5/10

#### Pozitíva
- SQLAlchemy 2.0 async pattern správne použitý
- Dobré indexy na foreign keys a query-kritických stĺpcoch
- Eager loading s `selectinload()` implementovaný
- Timezone-aware DateTime stĺpce

#### Návrhy na zlepšenie

**1. Pridať composite indexy pre časté queries:**
```python
# V models/job.py
class Job(Base):
    __table_args__ = (
        Index('ix_job_active_nextrun', 'is_active', 'next_run'),
        Index('ix_job_user_active', 'created_by', 'is_active'),
    )

# V models/job.py - JobExecution
class JobExecution(Base):
    __table_args__ = (
        Index('ix_execution_job_started', 'job_id', 'started_at'),
        Index('ix_execution_status_started', 'status', 'started_at'),
    )
```

**2. Pridať soft delete pattern:**
```python
class Script(Base):
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

**3. Optimalizovať N+1 queries v monitoring service:**
```python
# V monitoring_service.py - vždy používať selectinload
async def get_dashboard_data(self):
    agents = await self.session.execute(
        select(Agent).options(
            selectinload(Agent.script),
            selectinload(Agent.jobs).selectinload(Job.executions)
        )
    )
```

### 2.3 Security Implementation
**Hodnotenie:** 8.5/10

#### Pozitíva
- JWT authentication s argon2 password hashing
- Rate limiting implementovaný (slowapi)
- Path traversal protection
- Secret key validation pre production
- CORS správne nakonfigurovaný
- Comprehensive audit logging

#### Návrhy na zlepšenie

**1. Pridať request ID tracking:**
```python
# V core/middleware.py (nový súbor)
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# V main.py
app.add_middleware(RequestIDMiddleware)
```

**2. Implementovať password strength validation:**
```python
# V schemas/user.py
from pydantic import field_validator
import re

class UserCreate(BaseModel):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain special character')
        return v
```

**3. Pridať 2FA support (voliteľné):**
```python
# V models/user.py
class User(SQLAlchemyBaseUserTable[int], Base):
    totp_secret = Column(String(32), nullable=True)  # For TOTP 2FA
    totp_enabled = Column(Boolean, default=False)
    backup_codes = Column(JSON, nullable=True)  # Encrypted backup codes
```

### 2.4 Task Scheduling a Execution
**Hodnotenie:** 4/10 (neimplementované kritické časti)

#### Hlavné problémy
1. **Agent start/stop je len status update** - žiadna integrácia s Docker sandbox
2. **Job execution je mock** - simuluje okamžité dokončenie
3. **Chýba APScheduler integrácia** - jobs sa nespúšťajú automaticky
4. **Žiadny cron parser** - cron_expression sa ignoruje

#### Riešenia

**1. Implementovať APScheduler pre job scheduling:**
```python
# V services/scheduler_service.py (nový súbor)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        self.scheduler.start()
        await self._load_jobs()

    async def schedule_job(self, job: Job):
        if job.schedule_type == "cron":
            trigger = CronTrigger.from_crontab(job.cron_expression)
        elif job.schedule_type == "interval":
            trigger = IntervalTrigger(seconds=job.interval_seconds)
        else:  # once
            trigger = None

        self.scheduler.add_job(
            self._execute_job,
            trigger=trigger,
            id=f"job_{job.id}",
            args=[job.id],
            replace_existing=True
        )

    async def _execute_job(self, job_id: int):
        # Volať sandbox service pre spustenie scriptu
        pass

# V main.py
scheduler_service = SchedulerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    await scheduler_service.start()
    yield
    scheduler_service.scheduler.shutdown()
```

**2. Implementovať Docker agent execution:**
```python
# V services/agent_service.py
async def start_agent(self, agent_id: int, user: User) -> Optional[Agent]:
    agent = await self.get_agent(agent_id, user)
    if not agent:
        return None

    # Načítať script
    script = agent.script
    if not script:
        raise ValueError("Agent has no script assigned")

    # Spustiť v Docker sandboxe
    from .sandbox_service import SandboxService
    sandbox = SandboxService()

    try:
        container_id = await sandbox.run_script(
            script_content=script.content,
            script_path=script.file_path,
            timeout=None,  # Long-running agent
            env_vars=agent.config_json or {}
        )

        agent.status = "running"
        agent.config_json = agent.config_json or {}
        agent.config_json["container_id"] = container_id

        await self.session.commit()

    except Exception as e:
        agent.status = "error"
        await self.session.commit()
        raise

    return agent
```

**3. Pridať Celery pre background tasks (voliteľné, pre veľké nasadenia):**
```python
# V core/celery.py (nový súbor)
from celery import Celery

celery_app = Celery(
    'automa',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task
async def execute_job_task(job_id: int):
    # Async execution logic
    pass

# V pyproject.toml - pridať dependencies
# celery[redis]>=5.3.0
# redis>=5.0.0
```

### 2.5 Testing
**Hodnotenie:** 5/10

#### Súčasný stav
- 13 testov v backend/tests/
- Základné smoke tests pre endpointy
- 100% passing rate
- Test coverage ~15-20%

#### Návrhy

**1. Pridať integration tests:**
```python
# V tests/test_integration.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_workflow(client: AsyncClient, test_user):
    # 1. Register user
    response = await client.post("/auth/register", json={
        "email": "test@test.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201

    # 2. Login
    response = await client.post("/auth/jwt/login", data={
        "username": "test@test.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]

    # 3. Create script
    response = await client.post(
        "/api/v1/scripts/",
        json={"name": "Test Script", "content": "print('hello')"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    script_id = response.json()["id"]

    # 4. Create agent
    # 5. Create job
    # 6. Execute job
```

**2. Pridať service layer tests:**
```python
# V tests/test_service_logic.py
@pytest.mark.asyncio
async def test_agent_lifecycle():
    service = AgentService(session)

    # Create
    agent = await service.create_agent(agent_data, user)
    assert agent.status == "stopped"

    # Start
    agent = await service.start_agent(agent.id, user)
    assert agent.status == "running"

    # Stop
    agent = await service.stop_agent(agent.id, user)
    assert agent.status == "stopped"
```

**3. Nastaviť test coverage reporting:**
```bash
# V pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=backend/app --cov-report=html --cov-report=term-missing"
testpaths = ["tests"]

# Spustiť
uv run pytest --cov
```

---

## 3. Frontend Analýza

### 3.1 Architektúra
**Hodnotenie:** 7.5/10

#### Pozitíva
- Vue 3 Composition API správne použité
- Vuetify 3 pre Material Design
- Pinia state management
- Lazy loading routes
- Centralized API service s cachingom
- Dark mode support

#### Návrhy na zlepšenie

**1. Pridať loading states a error boundaries:**
```vue
<!-- V components/ErrorBoundary.vue (nový súbor) -->
<template>
  <div v-if="error" class="error-container">
    <v-alert type="error" prominent>
      <h3>Niečo sa pokazilo</h3>
      <p>{{ error.message }}</p>
      <v-btn @click="reset">Skúsiť znova</v-btn>
    </v-alert>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'

const error = ref(null)

onErrorCaptured((err) => {
  error.value = err
  return false
})

const reset = () => {
  error.value = null
}
</script>
```

**2. Optimalizovať API volania s debouncing:**
```javascript
// V utils/debounce.js (nový súbor)
export function debounce(fn, delay = 300) {
  let timeoutId
  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn.apply(this, args), delay)
  }
}

// Použitie v ScriptsView.vue
const searchScripts = debounce(async (query) => {
  const response = await apiService.scripts.list()
  scripts.value = response.data.filter(s =>
    s.name.toLowerCase().includes(query.toLowerCase())
  )
}, 300)
```

**3. Pridať WebSocket support pre real-time updates:**
```javascript
// V stores/websocket.js (nový súbor)
import { defineStore } from 'pinia'

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    socket: null,
    connected: false,
    messages: []
  }),

  actions: {
    connect() {
      this.socket = new WebSocket('ws://localhost:8000/ws')

      this.socket.onopen = () => {
        this.connected = true
      }

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.handleMessage(data)
      }
    },

    handleMessage(message) {
      if (message.type === 'agent_status_change') {
        // Update agent store
      } else if (message.type === 'job_execution_complete') {
        // Update job store
      }
    }
  }
})
```

### 3.2 State Management
**Hodnotenie:** 7/10

#### Súčasný stav
- Pinia store pre auth a theme
- Local component state pre data
- API service cache (5 min)

#### Návrhy

**1. Vytvoriť centrálne stores pre entities:**
```javascript
// V stores/scripts.js (nový súbor)
import { defineStore } from 'pinia'
import { apiService } from '@/services/api'

export const useScriptsStore = defineStore('scripts', {
  state: () => ({
    scripts: [],
    loading: false,
    error: null
  }),

  getters: {
    getScriptById: (state) => (id) => {
      return state.scripts.find(s => s.id === id)
    }
  },

  actions: {
    async fetchScripts() {
      this.loading = true
      try {
        const response = await apiService.scripts.list()
        this.scripts = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async createScript(scriptData) {
      const response = await apiService.scripts.create(scriptData)
      this.scripts.push(response.data)
      return response.data
    }
  }
})
```

### 3.3 Testing
**Hodnotenie:** 6/10

#### Súčasný stav
- 16 tests (všetky passing)
- Vitest + Vue Test Utils
- Unit tests pre stores a services

#### Návrhy

**1. Pridať component tests:**
```javascript
// V tests/components/ScriptDialog.test.js
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ScriptDialog from '@/components/ScriptDialog.vue'

describe('ScriptDialog', () => {
  it('validates required fields', async () => {
    const wrapper = mount(ScriptDialog, {
      props: { modelValue: true }
    })

    const saveBtn = wrapper.find('[data-test="save-btn"]')
    await saveBtn.trigger('click')

    expect(wrapper.find('.error-message').text()).toContain('Name is required')
  })

  it('emits save event with valid data', async () => {
    const wrapper = mount(ScriptDialog)

    await wrapper.find('#name-input').setValue('Test Script')
    await wrapper.find('#content-textarea').setValue('print("test")')
    await wrapper.find('[data-test="save-btn"]').trigger('click')

    expect(wrapper.emitted('save')).toBeTruthy()
    expect(wrapper.emitted('save')[0][0]).toEqual({
      name: 'Test Script',
      content: 'print("test")'
    })
  })
})
```

**2. Pridať E2E tests s Playwright (voliteľné):**
```javascript
// V tests/e2e/login.spec.js
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  await page.goto('http://localhost:8002')

  await page.fill('[data-test="email"]', 'test@test.com')
  await page.fill('[data-test="password"]', 'SecurePass123!')
  await page.click('[data-test="login-btn"]')

  await expect(page).toHaveURL('http://localhost:8002/dashboard')
  await expect(page.locator('h1')).toContainText('Dashboard')
})
```

---

## 4. Docker a Deployment

### 4.1 Súčasný stav
**Hodnotenie:** 8/10

#### Pozitíva
- Separátne docker-compose.yml a docker-compose.prod.yml
- Production má Docker socket proxy (bezpečnejšie)
- Environment variables správne použité
- Multi-stage builds (pravdepodobne)

#### Návrhy

**1. Optimalizovať Docker images:**
```dockerfile
# V docker/Dockerfile.backend
FROM python:3.13-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev

# Runtime stage
FROM python:3.13-slim

COPY --from=builder /app/.venv /app/.venv
COPY backend /app/backend

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Pridať health checks do docker-compose:**
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**3. Vytvoriť Kubernetes manifests (pre veľké nasadenia):**
```yaml
# V k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: automa-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: automa-backend
  template:
    metadata:
      labels:
        app: automa-backend
    spec:
      containers:
      - name: backend
        image: automa-backend:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /liveness
            port: 8000
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
```

---

## 5. Kritické TODO Items

### Priorita 1 (Blocker pre production)
1. **Implementovať Agent start/stop s Docker integráciou** (agent_service.py:112-149)
2. **Implementovať Job execution s sandbox** (job_service.py:128-136)
3. **Pridať APScheduler pre automatické job scheduling**
4. **Implementovať cron parsing** (job_service.py:23)

### Priorita 2 (Dôležité pre stabilitu)
5. **Zvýšiť test coverage na 60%+**
6. **Pridať retry logiku pre Docker operácie**
7. **Implementovať graceful shutdown pre agents**
8. **Pridať monitoring a alerting (Prometheus + Grafana)**

### Priorita 3 (Nice to have)
9. **Webový terminál pre debugging scriptov**
10. **Script versioning a rollback**
11. **Multi-tenancy support**
12. **API dokumentácia s examples (Swagger UI improvements)**

---

## 6. Performance Optimalizácie

### 6.1 Backend

**1. Pridať connection pooling pre PostgreSQL:**
```python
# V database.py (ak prejdete na PostgreSQL)
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

**2. Implementovať result pagination s cursor-based paging:**
```python
# V api/scripts.py
@router.get("/scripts/")
async def list_scripts(
    cursor: Optional[int] = None,
    limit: int = 50,
    service: ScriptService = Depends(get_script_service)
):
    scripts = await service.get_scripts_cursor(
        cursor=cursor,
        limit=limit
    )
    next_cursor = scripts[-1].id if len(scripts) == limit else None

    return {
        "items": scripts,
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None
    }
```

**3. Pridať Redis cache layer:**
```python
# V core/cache.py (nový súbor)
import redis.asyncio as redis
from functools import wraps

redis_client = redis.from_url("redis://localhost:6379")

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute and cache
            result = await func(*args, **kwargs)
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator
```

### 6.2 Frontend

**1. Implementovať virtual scrolling pre veľké listy:**
```vue
<!-- V ScriptsView.vue -->
<template>
  <v-virtual-scroll
    :items="scripts"
    :item-height="72"
    height="600"
  >
    <template v-slot:default="{ item }">
      <v-list-item :key="item.id">
        {{ item.name }}
      </v-list-item>
    </template>
  </v-virtual-scroll>
</template>
```

**2. Lazy load components:**
```javascript
// V router/index.js
const routes = [
  {
    path: '/scripts',
    component: () => import('@/views/ScriptsView.vue')  // ✅ Už máte
  },
  {
    path: '/monitoring',
    component: () => import('@/views/MonitoringView.vue')  // ✅ Už máte
  }
]
```

---

## 7. Code Quality Improvements

### 7.1 Linting a Formatting

**Pridať strict linting rules:**
```toml
# V pyproject.toml
[tool.ruff]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "T20", # flake8-print
    "SIM", # flake8-simplify
]
ignore = ["E501"]  # line too long

[tool.ruff.per-file-ignores]
"tests/*" = ["T20"]  # allow prints in tests
```

### 7.2 Type Hints

**Pridať type hints všade:**
```python
# Príklad - api/scripts.py
from typing import List, Optional

@router.get("/", response_model=List[ScriptRead])
async def list_scripts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: ScriptService = Depends(get_script_service)
) -> List[Script]:
    return await service.get_scripts(current_user, skip, limit)
```

**Spustiť mypy pre type checking:**
```bash
# V pyproject.toml - pridať dev dependency
# mypy>=1.7.0

# Konfigurácia
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 7.3 Documentation

**Pridať docstrings:**
```python
# Príklad - services/agent_service.py
async def start_agent(self, agent_id: int, user: User) -> Optional[Agent]:
    """
    Start an agent by launching its script in a Docker sandbox.

    Args:
        agent_id: The ID of the agent to start
        user: The user requesting the operation

    Returns:
        The updated Agent object with status "running", or None if not found

    Raises:
        ValueError: If agent has no script assigned
        DockerException: If container fails to start

    Example:
        >>> agent = await service.start_agent(123, current_user)
        >>> assert agent.status == "running"
    """
```

---

## 8. Bezpečnostné Odporúčania

### 8.1 Kritické

1. **Rotácia secret keys:**
```python
# V models/user.py
class SecretKey(Base):
    __tablename__ = "secret_keys"

    id = Column(Integer, primary_key=True)
    key_value = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

# Pri validácii JWT kontrolovať active keys
```

2. **Audit log retention policy:**
```python
# V services/audit_cleanup_service.py
async def cleanup_old_audit_logs(days: int = 90):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    await session.execute(
        delete(AuditLog).where(AuditLog.created_at < cutoff)
    )
```

3. **Implementovať API key authentication pre M2M:**
```python
# V models/api_key.py
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key_hash = Column(String(64), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
```

### 8.2 Odporúčané

4. **Session management s revokáciou:**
```python
# V models/session.py
class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token_jti = Column(String(36), unique=True)  # JWT ID
    created_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, default=False)
```

5. **Content Security Policy headers:**
```python
# V main.py
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["automa.local", "*.automa.local"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 9. Monitoring a Observability

### 9.1 Metriky (už máte Prometheus endpoint)

**Rozšíriť metriky:**
```python
# V core/metrics.py (nový súbor)
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'automa_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'automa_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Agent metrics
active_agents = Gauge(
    'automa_active_agents',
    'Number of active agents'
)

# Job metrics
job_executions = Counter(
    'automa_job_executions_total',
    'Total job executions',
    ['status']
)

job_duration = Histogram(
    'automa_job_duration_seconds',
    'Job execution duration'
)
```

### 9.2 Structured Logging

**Migrovať na strukturované loggovanie:**
```python
# V core/logging.py (nový súbor)
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Použitie
logger.info(
    "agent_started",
    agent_id=agent.id,
    user_id=user.id,
    container_id=container_id
)
```

### 9.3 Distributed Tracing

**Pridať OpenTelemetry:**
```python
# V main.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

FastAPIInstrumentor.instrument_app(app)
```

---

## 10. Akčný Plán (Roadmap)

### Fáza 1: Kritické Fixes ✅ COMPLETED (2025-09-30)
- [x] Implementovať Agent start/stop s Docker
- [x] Implementovať Job execution s sandbox
- [x] Pridať APScheduler integráciu
- [x] Implementovať cron parsing
- [x] Pridať retry logiku pre Docker operácie

**Výsledky:**
- Všetky TODO komentáre odstránené z production kódu
- Plne funkčný agent lifecycle management s Docker kontajnermi
- Reálna job execution s sandbox integráciou
- APScheduler automaticky načíta a spúšťa joby podľa rozvrhu
- Cron expressions plne podporované (croniter)
- Retry logika s exponenciálnym backoffom pre Docker operácie
- Všetky testy prechádzajú (13/13)

### Fáza 2: Stabilizácia ✅ COMPLETED (2025-09-30)
- [x] Optimalizovať databázové queries
- [x] Pridať composite indexy
- [x] Implementovať soft delete pattern
- [x] Vytvoriť database migration script
- [ ] Zvýšiť test coverage na 60%+ (ďalšia iterácia)
- [ ] Pridať integration tests (ďalšia iterácia)
- [ ] Implementovať graceful shutdown (ďalšia iterácia)

**Výsledky:**
- Composite indexy pre všetky kritické queries
- Soft delete pattern pre Script, Agent, Job modely
- Database schema migration úspešne dokončený
- Všetky testy prechádzajú (13/13)

### Fáza 3: Performance ✅ COMPLETED (2025-09-30)
- [x] Pridať Redis cache
- [x] Implementovať WebSocket pre real-time updates
- [x] Frontend virtual scrolling (už implementované cez v-data-table)
- [ ] Implementovať connection pooling (PostgreSQL) - nie je potrebné pre SQLite

**Výsledky:**
- Redis cache vrstva s automatickým fallbackom
- WebSocket endpoint s connection managerom
- Pinia store pre WebSocket management
- Cache monitoring endpointy
- Event-based architektúra pre real-time updates
- Všetky testy prechádzajú (13/13)

### Fáza 4: Security Hardening (1-2 týždne)
- [ ] Password strength validation
- [ ] Session management s revokáciou
- [ ] API key authentication
- [ ] Security headers middleware
- [ ] Secret key rotation

### Fáza 5: Observability (1 týždeň)
- [ ] Rozšíriť Prometheus metriky
- [ ] Structured logging
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Alerting rules (Prometheus AlertManager)

### Fáza 6: Developer Experience (1 týždeň)
- [ ] Type hints všade + mypy
- [ ] Complete docstrings
- [ ] API documentation improvements
- [ ] Development tooling (pre-commit hooks)

---

## 11. Odhadované Náklady

### Časové odhady
- **Kritické fixes:** 40-80 hodín
- **Stabilizácia:** 60-100 hodín
- **Performance:** 40-60 hodín
- **Security:** 30-50 hodín
- **Observability:** 20-30 hodín
- **DX improvements:** 15-25 hodín

**Celkom:** 205-345 hodín (~5-8 týždňov pri full-time práci)

### Infraštruktúra (mesačne)
- **Development:** $0 (local Docker)
- **Staging:** $20-50 (VPS + Redis)
- **Production (malé):** $50-100 (VPS + Redis + monitoring)
- **Production (stredné):** $200-500 (Kubernetes cluster + managed services)

---

## 12. Záver

Automa je **solídny projekt s dobrými základmi**. Hlavné oblasti na zlepšenie:

1. **Implementovať chýbajúcu business logiku** (agent lifecycle, job execution)
2. **Zvýšiť test coverage** na minimum 60%
3. **Optimalizovať performance** (indexy, caching, connection pooling)
4. **Hardening security** (password validation, 2FA, API keys)
5. **Zlepšiť observability** (metriky, tracing, structured logging)

**Odporúčanie:** Začať s Fázou 1 (Kritické Fixes), pretože bez implementovanej agent/job execution logiky je aplikácia len "shell" bez skutočnej funkcionality.

Po dokončení Fázy 1-2 bude aplikácia **production-ready** pre malé až stredné nasadenia.

---

## 13. Kontaktné Body pre Review

Pre akékoľvek otázky k tejto analýze:
- **Backend architektúra:** Sekcia 2
- **Frontend architektúra:** Sekcia 3
- **Security concerns:** Sekcia 8
- **Performance:** Sekcia 6
- **Roadmap:** Sekcia 10

**Dátum nasledujúceho review:** +3 mesiace (alebo po dokončení Fázy 2)
