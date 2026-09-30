# 1–4. Explanation, Industry Relevance, Cloud Concepts, Stack Options

## 1. Project explanation
**A. Simple:** It is a personal notebook for hobbies (guitar, photography, coding…) that lives on the internet. You set a goal ("practice 30 hours"), log each practice, watch a progress bar fill, upload a photo as proof, and share the win with a community that can like and comment. Because it is stored centrally, you see the same data on your phone and laptop.

**B. Technical:** A client–server web app. The browser SPA calls a stateless REST API (FastAPI). The API authenticates users with signed JWTs, keeps relational data (users, skills, goals, sessions, posts…) in a database, keeps file bytes in object storage (DB keeps only `storage_key` + metadata), and computes analytics with SQL + pure Python functions.

**Workflow**
```
User → Register/Login → JWT issued (Authentication)
     → Create Skill → Set Goal (+milestones) → Log Practice
     → DB write → progress = min(100, current/target×100); milestones/goal auto-complete; streak recomputed
     → Upload proof → validated (size, magic bytes) → object storage; metadata row in DB
     → Create Post (text + skill + file_id) → Community Feed (JOIN users/skills/files, counts of likes/comments)
     → Others like (PK(post_id,user_id) = no duplicates) / comment → owner sees engagement in dashboard
```
* **Cross-device:** data lives on the server, the device only holds a token.
* **Feed:** `SELECT posts JOIN users … ORDER BY created_at DESC LIMIT/OFFSET` with subquery counts.
* **Analytics:** total minutes/60, last-7-day and calendar-month sums, 8-week and 6-month trends, streaks (see `analytics/progress_service.py`).
* **Streak rule:** distinct practice days; consecutive calendar days ending today *or yesterday* (you still have today to continue). Several sessions in a day = 1 day. Dates are UTC/server-local, a known limitation.

## 2. Industry relevance
| Domain | Same pattern |
|---|---|
| Learning platforms / LMS / EdTech | courses → skills, assignments → goals, completion analytics |
| Fitness apps | workouts = practice sessions, streaks, shareable achievements |
| Professional skill / employee learning portals | manager dashboards on the same skill/goal tables |
| Creator & online communities, social apps | user-generated content + feed + likes/comments |
| Portfolio platforms | proof uploads (certificates/screenshots) in object storage |

Business benefits: centralized user data, cross-device access, engagement (community), scalable media storage, UGC, analytics-driven personalization, easy collaboration.

## 3. Where each cloud concept appears
| Concept | Where in this project |
|---|---|
| Cloud computing | app + data + files hosted remotely and reached over HTTP |
| SaaS | the finished app users just open in a browser |
| PaaS | deploying backend to a platform host (Render/Railway/App Runner/Cloud Run) without managing servers |
| IaaS | Option C: EC2/VM, S3 buckets, VPC – you assemble the infrastructure |
| Cloud database | `cloud/database_service.py` (SQLite locally → PostgreSQL/RDS/Supabase) |
| Object storage | `cloud/storage_service.py` (local folder → S3/R2/Supabase Storage) |
| Authentication | JWT login (`cloud/auth_service.py`), PBKDF2 password hashing |
| Authorization | ownership checks (`owned_skill`, delete post/comment), admin flag, 404 for others' data |
| REST API / client-server | `/api/*` routes in `backend/routes`, SPA in `frontend/` |
| Serverless | Option C: same FastAPI via Lambda (Mangum) or thumbnail-on-upload function |
| Event-driven | Option C: S3 upload event → function (virus scan/resize); notifications on like/comment |
| Scalability / elasticity | stateless API ⇒ add instances; managed DB and storage scale separately |
| Availability | multiple instances behind a load balancer, managed DB backups/replicas, `/health` endpoint |
| CDN | put CloudFront/Cloudflare in front of storage + frontend (Option C) |
| Load balancing | platform LB / ALB distributes requests across API instances |
| API gateway | Option C: API Gateway (throttling, auth, routing); locally: our rate limiter |
| Caching | feed/trending cached in Redis/ElastiCache (Option C); `Cache-Control` on images (implemented) |
| Environment variables / secrets | `.env`, `backend/utils/config.py`; platform secret stores in deployment |
| Logging / monitoring | Python `logging` (implemented), `/health`; CloudWatch/Grafana in cloud |
| Backup | DB snapshots/PITR (managed DB), bucket versioning |
| CI/CD | GitHub Actions running `pytest` then deploying (`docs/05_github_and_proof.md`) |
| Cloud deployment | `docs/03_run_and_deploy.md` |

## 4. Stack options
| | **A – Beginner** | **B – Recommended cloud** | **C – Advanced** |
|---|---|---|---|
| Frontend | HTML/CSS/JS (this repo) | React (Vite) | React/Next.js on S3+CloudFront |
| Backend | FastAPI (Flask equivalent) | FastAPI | FastAPI on Lambda/App Runner |
| Auth | own JWT | Supabase Auth / Firebase Auth | Cognito |
| DB | SQLite | Supabase PostgreSQL / Firestore | RDS / DynamoDB |
| Files | local folder | Supabase Storage / Firebase Storage | S3 + CloudFront |
| Difficulty | Easy | Medium | Hard |
| Cost | free | free tier (check current limits) | pay-per-use; free tier limited, set budget alerts |
| Concepts shown | REST, auth, DB, storage design | + managed DB/auth/storage, PaaS deploy | + CDN, gateway, serverless, cache, monitoring |
| Limits | not really "cloud", not scalable | vendor lock-in, free-tier sleeps/limits | complexity, cost risk |

**Recommendation for a student:** build/run **A** first (this repo, fully working), then move to **B** by switching only the *cloud/* layer: object storage via the S3-compatible setting (`STORAGE_BACKEND=s3`), database to PostgreSQL. Describe **C** in the report as the scaling design. That gives working proof + cloud story without payment risk.
