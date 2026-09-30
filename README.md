# Online Hobby & Skills Tracker with Community Sharing on Cloud

![python](https://img.shields.io/badge/python-3.10+-blue) ![api](https://img.shields.io/badge/API-FastAPI-009688) ![tests](https://img.shields.io/badge/tests-pytest-green)

## Overview
Track hobbies and skills, set goals with milestones, log practice, upload proof and share achievements in a community feed. Built to demonstrate **cloud computing architecture**: stateless REST API, authentication/authorization, database, object storage with signed URLs, analytics, security, scalability and failure handling. Uses synthetic data only.

## Problem Statement
Learners keep progress in scattered notes with no accountability, analytics or community, and no cross-device access.

## Objectives
Centralized cloud data · secure user accounts · goal/practice analytics · file storage · community engagement · tested, documented, deployable project.

## Features
Register/login/logout (JWT) · profiles (public/private, avatar) · skills (levels/status) · goals + milestones · practice logging (auto progress, streaks) · uploads · posts, feed (filter/search/sort/following), likes, comments, follows, reports · analytics dashboard (5 charts) · REST API + Swagger.

## Industry Relevance
LMS/EdTech, fitness apps, employee learning portals, creator communities, portfolio platforms → `docs/01_concepts_and_options.md`.

## Cloud Computing Concepts
Concept → location table in `docs/01_concepts_and_options.md`.

## Architecture
```
Browser SPA → REST API (FastAPI, stateless, JWT) ─┬→ Database (SQLite → PostgreSQL)
                                                  ├→ Object Storage (local → S3/R2/Supabase, signed URLs)
                                                  └→ Analytics (SQL + progress_service)
```
Advanced design (CDN, API Gateway, Lambda/App Runner, RDS, S3, Redis, CloudWatch): `docs/03_run_and_deploy.md`.

## Technology Stack
Python, FastAPI, Pydantic, PyJWT, SQLite, boto3 (optional S3), vanilla JS, pytest.

## User Profiles / Hobby & Skill Tracking / Practice / Goals & Milestones
See `backend/routes/{profile,skills,practice}.py` and `backend/services/tracking_service.py`. Progress % = `min(100, current/target×100)`; streak = consecutive practice days ending today or yesterday.

## Cloud Database / Object Storage
Schema + ER diagram: `cloud/database_service.py`, `docs/02_design.md`. Storage: `cloud/storage_service.py` (`STORAGE_BACKEND=local|s3`).

## Community Sharing / Likes & Comments / Analytics
`backend/routes/{posts,social,analytics}.py`, `analytics/progress_service.py`.

## REST APIs
Full table in `docs/02_design.md`; live docs at `/docs`.

## Folder Structure
```
frontend/  backend/{app.py,routes,models,services,middleware,utils}/  cloud/  analytics/
tests/  sample_data/  screenshots/  docs/  reports/  README.md  requirements.txt  .env.example
```

## Installation & Local Setup
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # set SECRET_KEY
uvicorn backend.app:app --reload                       # http://localhost:8000
python sample_data/seed.py                             # optional synthetic users/content
```

## Environment Variables
`SECRET_KEY` (required), `TOKEN_EXPIRE_MINUTES`, `DATABASE_PATH`, `CORS_ORIGINS`, `MAX_UPLOAD_MB`, `RATE_LIMIT_PER_MIN`, `SIGNED_URL_SECONDS`, `STORAGE_BACKEND`, `LOCAL_UPLOAD_DIR`, `S3_*` – see `.env.example`.

## Cloud Deployment
Free-tier and AWS reference deployment steps: `docs/03_run_and_deploy.md`. **Live demo:** _add URL after you deploy_.

## Testing
`python -m pytest -v` → 19 tests (auth, isolation, uploads, feed, likes, analytics, failures). Test matrix: `docs/04_testing_security_scale.md`.

## Security / Privacy / Scalability / Failure Handling
`docs/04_testing_security_scale.md`.

## Screenshots
_Add files from `screenshots/` (checklist in `docs/05_github_and_proof.md`)._

## Results
Local end-to-end flow verified: register → skill → goal → practice → progress/milestone → upload → post → like/comment → dashboard.

## Limitations
SQLite default (use PostgreSQL for real deployments), in-memory rate limiter, plain-JS UI, no email verification/blocking/moderation queue, UTC-naive streaks.

## Future Improvements
Managed auth and Postgres, React UI, Redis cache, notifications, moderation, idempotency keys, CDN.

## Learning Outcomes
Cloud service boundaries, secure API design, object storage patterns, analytics design, testing failure paths, CI/CD.

## Author
_Your name · GitHub · LinkedIn_
