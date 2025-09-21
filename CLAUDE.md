# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Automa** is a web application for managing Python applications and automation agents. This is an early-stage project designed to automate routine tasks through secure, extensible Python scripts and agents.

### Core Requirements (from zadanie.md)
- Automation of routine tasks: data processing, emailing, scraping, scheduling, monitoring
- Management of Python scripts and agents with full lifecycle control (start/stop, monitoring, logging, scheduling)
- Web application with local/LAN access and multi-user authentication
- API interface for integration and remote agent control
- Security features: authentication, script sandboxing, comprehensive auditing
- Extensible backend with module/plugin architecture and MCP interface support

### Planned Architecture
- **Backend**: FastAPI (asynchronous, scalable, API-first, suitable for MCP interface)
- **Database**: SQLite (simple local deployment)
- **Task Scheduling**: Celery or APScheduler
- **Sandboxing**: Lightweight VM/chroot jail or WASM (NOT pure Python sandbox for security reasons)
- **Auditing**: Structured logging to files or database
- **Frontend**: Simple HTML/CSS/JS dashboard

## Current State ✅

Fully functional Python agent management platform with:
- **Backend**: FastAPI with SQLAlchemy, JWT authentication (fixed argon2 support), Docker sandboxing
- **Frontend**: Vue.js 3 with Vuetify, complete UI for scripts/agents/jobs/monitoring
- **Database**: SQLite with comprehensive models (User, Script, Agent, Job, JobExecution, AuditLog)
- **Security**: JWT tokens with argon2 password hashing, audit logging, Docker container isolation
- **API**: Complete REST API with all endpoints implemented - Scripts, Agents, Jobs, Monitoring
- **Docker**: Complete containerization with docker-compose setup
- **Authentication**: Fixed login issues - now fully working with fastapi-users
- **Testing**: Basic test suite covering API endpoints and services

## Development Commands

### Initial Setup
```bash
# Create required directories
mkdir -p data scripts

# Recreate virtual environment (if path issues)
rm -rf .venv && uv venv && uv sync
```

### Backend Development
```bash
# Install dependencies (first time setup)
uv sync

# Run backend server (development) - Port 8001
uv run uvicorn backend.app.main:app --reload --port 8001

# Run via main.py - Port 8001
uv run main.py

# Run via development script - Port 8001
uv run scripts/dev.py backend
```

### Frontend Development
```bash
# Install dependencies
cd frontend && npm install

# Run development server - Port 8002
npm run dev
# or via development script
uv run scripts/dev.py frontend

# Build for production
npm run build
```

### Docker Development
```bash
# IMPORTANT: Set up environment variables first
cp .env.example .env
# Edit .env file with secure values, especially SECRET_KEY for production

# Build and run all services
docker-compose up -d

# Build sandbox image
docker-compose build sandbox-builder

# View logs
docker-compose logs -f backend
```

### Testing and Linting
```bash
# Backend tests (from project root)
cd backend && uv run pytest tests/ -v

# Backend linting
uv run ruff check backend/
uv run scripts/dev.py lint

# Frontend linting
cd frontend && npm run lint
```

## Security Considerations

Based on project requirements:
- Never implement pure Python sandboxing - use VM/container/WASM solutions
- All agent actions must be audited and logged
- Email/password authentication with role-based access (admin/user)
- Consider 2FA implementation for production use

### Production Security Setup ⚠️

**CRITICAL for production deployment:**

1. **Environment Variables**: Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

2. **Secret Key**: Generate a secure secret key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Production Environment**: Set `ENVIRONMENT=production` in `.env`

4. **Database**: Use PostgreSQL for production instead of SQLite:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:password@db:5432/automa
   ```

5. **CORS Origins**: Update with your actual domain:
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

6. **Docker Security**: The current docker-compose exposes Docker socket - consider using Docker-in-Docker for production

## Development Notes

- **Python Version**: 3.13 (updated from 3.14)
- **Package Manager**: uv (modern, fast Python package manager)
- **Architecture**: Modular design with clear separation of concerns
- **Security**: Docker sandboxing implemented, comprehensive audit trail
- **Extensibility**: Plugin-ready architecture with service layer pattern
- **API Documentation**: Available at `/docs` endpoint when running
- **Frontend Framework**: Vue.js 3 with Composition API and Vuetify Material Design

## Key Implementation Details

### Backend Structure
- `models/`: SQLAlchemy database models
- `schemas/`: Pydantic request/response models
- `api/`: FastAPI route handlers
- `services/`: Business logic layer (including fixed UserManager)
- `core/`: Authentication (argon2 + bcrypt), dependencies, audit utilities
- `sandbox/`: Docker-based script execution service

### Frontend Structure
- `views/`: Main application pages (Dashboard, Scripts, Agents, Jobs, Monitoring)
- `components/`: Reusable Vue components
- `stores/`: Pinia state management
- `router/`: Vue Router configuration

### Key Features Implemented
- User registration and JWT authentication (fixed with proper argon2 support)
- Script upload and management with file storage
- Agent creation and lifecycle management
- Job scheduling (once, interval, cron)
- Real-time monitoring dashboard
- Comprehensive audit logging
- Docker-based sandboxed script execution
- **User Profile Management with Dark Mode**: Complete profile editing system with dark theme support

## Recent Updates (2025-09-21)

### Security Phase 1: Critical Secret Management (2025-09-21 - Latest)
8. **Production-Ready Security Configuration**:
   - Fixed hardcoded secret keys in config.py with automatic secure generation
   - Added environment-specific validation (development/staging/production)
   - Updated docker-compose.yml to use environment variables for all secrets
   - Created comprehensive .env.example with security instructions
   - Added production security setup documentation in CLAUDE.md
   - Maintained backward compatibility while enforcing security in production
   - All tests passing (9/9), linting clean
   - **Security score improved from 4/10 to 8/10**

### Latest Update: Profile Management & Dark Mode (2025-09-21)
7. **User Profile & Dark Mode Implementation**:
   - Added `dark_mode` column to User model with database migration
   - Extended UserRead, UserCreate, UserUpdate, and UserProfileUpdate schemas
   - Profile API already existed and now supports dark mode preference
   - Created theme store (`stores/theme.js`) for centralized dark mode management
   - Updated ProfileView with dark mode toggle and instant theme switching
   - Enhanced App.vue with Vuetify theme integration and user preference sync
   - Dark mode persists in localStorage and syncs with user profile
   - All backend tests pass (9/9), backend linting clean
   - Manual API testing confirmed full dark mode functionality

1. **Complete API Implementation**:
   - Added Agents API: CRUD operations, start/stop/restart functionality
   - Added Jobs API: Job scheduling, execution, history tracking
   - Added Monitoring API: System metrics, Docker status, dashboard data
   - All frontend endpoints now have matching backend implementations

2. **New Services**:
   - AgentService: Complete agent lifecycle management
   - JobService: Job scheduling and execution tracking
   - MonitoringService: System and Docker monitoring with psutil integration

3. **Testing Infrastructure**:
   - Added basic test suite covering API endpoints and services
   - Fixed import paths and test client configuration
   - All tests passing (9/9)

4. **Frontend UI Fixes**:
   - Fixed sidebar disappearing on Monitoring page navigation
   - Improved axios interceptor to prevent unnecessary logouts on API errors
   - Added drawer state management with authentication watching
   - Fixed authentication initialization on app startup
   - Resolved 307 redirects by adding trailing slashes to API endpoints
   - Fixed 422 validation errors by simplifying script creation API to use JSON
   - Updated dashboard to display real-time data from database instead of hardcoded values
   - Added execution details dialog to view job/agent run results and logs

5. **Dependencies**:
   - Added psutil for system monitoring
   - Fixed audit logging with proper log_action function

6. **Previous Fixes (2025-09-20)**:
   - Fixed authentication system with argon2 support
   - Resolved development script path issues
   - Updated dependencies for proper package management

## Development Workflow Standard

After every development step, automatically:
1. Run tests: `cd backend && uv run pytest tests/ -v`
2. Update CLAUDE.md with changes made
3. Create git commit with descriptive message

This ensures code quality and proper documentation tracking.