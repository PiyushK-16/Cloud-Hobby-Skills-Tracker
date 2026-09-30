# 20–21. Run locally and deploy

## Local run (Windows: use `py` and `venv\Scripts\activate`)
```bash
# 1-2 Install Python 3.10+, then:
cd Cloud-Hobby-Skills-Tracker
python -m venv .venv && source .venv/bin/activate
# 3-4 Dependencies (frontend needs no npm install in Option A)
pip install -r requirements.txt
# 5 Configure
cp .env.example .env      # then set SECRET_KEY (command is in the file)
# 6-7 Start backend (also serves the frontend)
uvicorn backend.app:app --reload --port 8000
# open http://localhost:8000   (API docs: /docs)
```
Expected: `Uvicorn running on http://127.0.0.1:8000`; `GET /health` → `{"status":"ok"}`.
Optional synthetic data: `python sample_data/seed.py` (users `asha`, `ben`, `chloe`, password printed by script).

**Walkthrough (steps 8-20)**
1. Register **User A** (e.g. `usera`) → login. 2. Skills → add *Photography*. 3. Goals → 20 hours, milestones `1,5,10,20`.
4. Practice → 60 minutes. 5. Goals page: `1 / 20 hours · 5%`, milestone "1 hours" ✅ (toast "🎉 Milestone").
6. Community → write post, choose skill *Photography*, attach a PNG/JPG → Post.
7. Log out, register **User B** → Community shows A's post with image. 8. B clicks ❤️ and comments.
9. Log in as A → post shows 1 like, 1 comment; Dashboard shows *Likes 1, Comments 1, Total practice 1 h, Streak 1*.
10. As B, Skills page is empty → user-data isolation. Terminal proof: `curl -H "Authorization: Bearer <B token>" localhost:8000/api/skills/<A skill id>` → 404.

## Approach A – free-tier / student
Verify each provider's *current* free-tier limits before starting; they change.
1. **Storage (files):** create a free bucket on an S3-compatible service (Supabase Storage or Cloudflare R2). Create S3 access keys; set `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_REGION`. Keep the bucket **private** – the app hands out signed URLs. No code change.
2. **Database:** SQLite needs a persistent disk. Free web hosts often have ephemeral disks (data resets on redeploy). Two choices: (a) host with a persistent volume and keep SQLite (fine for demo); (b) move to a free managed PostgreSQL (Supabase/Neon): reimplement `cloud/database_service.py` with `psycopg` (replace `?` with `%s`, `INSERT OR IGNORE` with `ON CONFLICT DO NOTHING`, `EXISTS(...)` booleans, `strftime` in logout). Route code stays the same. This migration is **not included** and is a good "future work"/stretch task.
3. **Backend + frontend (one service):** push repo to GitHub → create a Web Service on Render/Railway/Fly.io (PaaS) → build `pip install -r requirements.txt` → start `uvicorn backend.app:app --host 0.0.0.0 --port $PORT` → add env vars in the dashboard (never in Git): `SECRET_KEY`, `CORS_ORIGINS=https://<your-app-url>`, storage vars, `DATABASE_PATH` (on the persistent volume path).
4. **Auth:** built in (JWT). Managed auth (Supabase/Firebase) is the Option B swap.
5. Open the URL, repeat the walkthrough, screenshot the host dashboard + live app.

## Approach B – enterprise (AWS example)
```
Route53 → CloudFront → S3 (static frontend)
                  └→ API Gateway (throttling, JWT authorizer=Cognito) → Lambda (FastAPI+Mangum) / App Runner
                                                     ├→ RDS PostgreSQL (or DynamoDB)
                                                     ├→ S3 media bucket (private, presigned URLs, CloudFront OAC)
                                                     ├→ ElastiCache Redis (feed/trending cache, optional)
                                                     └→ CloudWatch logs/metrics/alarms; Secrets Manager; S3 event → Lambda (scan/resize)
```
Azure equivalents: Static Web Apps/Blob+CDN, API Management, Functions/App Service, Azure SQL/Cosmos DB, Blob Storage, Entra ID B2C, Azure Monitor. GCP: Cloud Storage+CDN, API Gateway, Cloud Run/Functions, Cloud SQL/Firestore, Firebase Auth/Identity Platform, Cloud Monitoring.
Cost safety: set a budget alert first, use free tier, delete resources after taking screenshots.
