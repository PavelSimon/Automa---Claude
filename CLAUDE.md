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

## Recent Updates (2025-09-21)

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