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

## Credential Management System Implementation Plan (2025-09-27)

### Overview
Secure credential management system for storing and managing authentication data used by scripts and agents.

### Architecture
- **Encryption**: Fernet symmetric encryption with user-derived keys
- **Key Management**: Master key derived from user password + salt
- **Storage**: Encrypted JSON blobs in database
- **Access Control**: User-scoped credentials with role-based permissions

### Database Models

#### Credential Model
```python
class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    credential_type = Column(String(50), nullable=False)  # api_key, user_pass, oauth, ssh_key, db_connection, custom
    encrypted_data = Column(LargeBinary, nullable=False)  # Encrypted JSON data
    encryption_key_id = Column(String(100), nullable=False)  # Key version for rotation
    tags = Column(JSON)  # For categorization ["aws", "production", "email"]
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))

    # Relationships
    creator = relationship("User", backref="credentials")
    script_credentials = relationship("ScriptCredential", back_populates="credential")
```

#### Script-Credential Association
```python
class ScriptCredential(Base):
    __tablename__ = "script_credentials"

    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    credential_id = Column(Integer, ForeignKey("credentials.id"), nullable=False)
    variable_name = Column(String(100), nullable=False)  # Environment variable name
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    script = relationship("Script", backref="script_credentials")
    credential = relationship("Credential", back_populates="script_credentials")
```

### API Endpoints
```
# Credential Management
POST   /api/v1/credentials/                           # Create new credential
GET    /api/v1/credentials/                           # List user's credentials (metadata only)
GET    /api/v1/credentials/{credential_id}            # Get credential details (no sensitive data)
PUT    /api/v1/credentials/{credential_id}            # Update credential
DELETE /api/v1/credentials/{credential_id}            # Delete credential
POST   /api/v1/credentials/{credential_id}/decrypt    # Decrypt credential data (requires user password)
POST   /api/v1/credentials/{credential_id}/test       # Test credential validity
GET    /api/v1/credentials/types                      # Get supported credential types

# Script-Credential Associations
GET    /api/v1/scripts/{script_id}/credentials        # Get script's credentials
POST   /api/v1/scripts/{script_id}/credentials        # Assign credential to script
DELETE /api/v1/scripts/{script_id}/credentials/{credential_id}  # Remove assignment
```

### Frontend Components
1. **CredentialsView.vue** - Main credentials management page
2. **CredentialDialog.vue** - Create/edit modal with type-specific forms
3. **CredentialTypeCards.vue** - Visual cards for different credential types
4. **ScriptCredentialAssignment.vue** - Assign credentials to scripts

### Security Features
- **Encryption at Rest**: All sensitive data encrypted with Fernet
- **User-Scoped Keys**: Each user has unique encryption key derived from password
- **No Plain Text**: Sensitive data never stored unencrypted
- **Rate Limiting**: Decrypt operations rate limited
- **Audit Trail**: All credential operations logged
- **Session Security**: Auto-clear clipboard, session timeouts
- **Key Rotation**: Support for encryption key rotation

### Supported Credential Types
1. **API Keys** - Single API key with optional headers
2. **Username/Password** - Basic authentication credentials
3. **OAuth Tokens** - Access/refresh token pairs with expiration
4. **SSH Keys** - Public/private key pairs
5. **Database Connections** - Connection strings and credentials
6. **Custom** - Flexible JSON structure for any credential type

### Implementation Priority
1. Database models and migrations
2. Encryption service and key management
3. Backend API endpoints
4. Frontend UI components
5. Script integration for environment variable injection
6. Testing and security audit

### Files to Create/Modify
- `backend/app/models/credential.py`
- `backend/app/schemas/credential.py`
- `backend/app/api/credentials.py`
- `backend/app/services/credential_service.py`
- `backend/app/services/encryption_service.py`
- `frontend/src/views/CredentialsView.vue`
- `frontend/src/components/CredentialDialog.vue`
- Database migration scripts

## Development Workflow Standard

After every development step, automatically:
1. Run tests: `cd backend && uv run pytest tests/ -v`
2. Update CLAUDE.md with changes made
3. Create git commit with descriptive message

This ensures code quality and proper documentation tracking.