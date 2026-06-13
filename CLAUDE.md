# Overhang — 3D Model Library

## Architecture
- Backend: FastAPI (Python 3.12), port 8000
- Frontend: Vue 3 + Tailwind + Vite, served via Nginx, port 80
- DB: MariaDB 11
- Task Queue: Celery + Redis
- Deployment: Docker Compose on overhang01.pe.lan (10.10.1.18)

## Services
- `backend` — FastAPI app, REST API under /api/
- `worker` — Celery worker for async scraping jobs
- `frontend` — Nginx serving Vue 3 build, proxies /api/ to backend
- `db` — MariaDB, init via backend/migrations/init.sql
- `redis` — Celery broker + result backend

## File Storage
- Docker volume `files_data` mounted at /app/storage
- Subdirs per model: /app/storage/{model_id}/images/, /app/storage/{model_id}/files/

## Key conventions
- All secrets in `.env` (see `.env.example`)
- DB migrations: manual SQL in backend/migrations/
- Commit messages: English, imperative
- CORS: open in dev, restrict in production

## Current state
- [x] Phase 1: Grundgerüst (Docker Compose, DB schema, FastAPI skeleton, Vue skeleton)
- [ ] Phase 2: Scraper MVP (Printables + Thingiverse)
- [ ] Phase 3: Bibliothek-UI (Liste, Detailansicht, Suche)
- [ ] Phase 4: 3D-Viewer (Three.js)
- [ ] Phase 5: Slicer-Integration
- [ ] Phase 6: Auth + Multi-User
- [ ] Phase 7: MakerWorld-Scraper (Playwright)
