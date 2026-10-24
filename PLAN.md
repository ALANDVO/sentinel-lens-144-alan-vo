# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

foundation

## Roadmap

### foundation — Project Foundation & Skeleton

Status: done

Acceptance:
- Repository has all required root files (README.md, LICENSE, CHANGELOG.md, pyproject.toml, .gitignore, .env.example, compose.yaml, portfolio.json)
- Backend has FastAPI skeleton with main.py, requirements.txt, Dockerfile
- Frontend has React+TypeScript+Vite skeleton with package.json, package-lock.json, Dockerfile
- CI workflow exists with backend/frontend test and build jobs
- Project builds and tests pass (even if minimal)

Implementation: `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `.gitignore`, `.env.example`, `compose.yaml`, `portfolio.json`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/app/main.py`, `backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/app/db/__init__.py`, `backend/app/api/__init__.py`, `backend/app/api/routes.py`, `backend/app/models/__init__.py`, `backend/app/models/audit.py`, `backend/app/models/finding.py`, `backend/app/models/coverage.py`, `backend/app/models/user.py`, `backend/app/services/__init__.py`, `backend/app/services/audit_engine.py`, `backend/tests/__init__.py`, `backend/tests/test_main.py`, `backend/tests/test_audit_engine.py`, `backend/Dockerfile`, `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/src/api/client.ts`, `frontend/src/context/AuthContext.tsx`, `frontend/src/hooks/useAuth.ts`, `frontend/src/components/Navbar.tsx`, `frontend/src/pages/AuditList.tsx`, `frontend/src/pages/NewAudit.tsx`, `frontend/src/pages/AuditDetail.tsx`, `frontend/src/pages/Login.tsx`, `frontend/src/test/setup.ts`, `frontend/src/App.test.tsx`, `frontend/Dockerfile`, `frontend/nginx.conf`, `keycloak/realm.json`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_main.py`, `backend/tests/test_audit_engine.py`, `frontend/src/App.test.tsx`

### auth — OIDC Authentication with Keycloak

Status: planned

Acceptance:
- Backend has OIDC auth routes (login, callback, logout, me)
- Frontend has login page and protected routes
- Keycloak integration in compose.yaml
- Tokens validated with signature/issuer/audience checks
- Role-based access control (viewer, operator, admin)

### audit-engine — Security Audit Domain Engine

Status: planned

Acceptance:
- Core audit engine with multi-phase workflow (recon, hunting, validation, reporting)
- Coverage ledger and findings models
- Deterministic offline analysis without LLM
- LLM explanations as opt-in advisory

### workflows — Three Complete User Workflows

Status: planned

Acceptance:
- Workflow 1: Create new audit run with target repository
- Workflow 2: Import and review prior audit findings
- Workflow 3: Search/export findings with filters
- All workflows functional end-to-end

### docs — Documentation & Polish

Status: planned

Acceptance:
- README with install/run/test steps, architecture diagram, API reference
- CHANGELOG with actual changes
- API docs in docs/
- All portfolio.json fields populated correctly

