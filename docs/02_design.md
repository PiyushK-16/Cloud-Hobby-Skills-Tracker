# 5–18. Design: modules, database, storage, APIs, architecture, folders

## Database (ER text diagram)
```
USERS 1───* SKILLS 1───* GOALS 1───* MILESTONES
  │  1        │ 1
  │  └───* PRACTICE_SESSIONS (user_id, skill_id)
  │
  ├──1───* POSTS *───0..1 SKILLS      POSTS *───0..1 FILES      POSTS *───0..1 MILESTONES
  │           1───* COMMENTS (user_id)     1───* LIKES  PK(post_id,user_id)     1───* REPORTS
  ├──1───* FILES (storage_key)
  └──*───* USERS via FOLLOWS PK(follower_id, following_id)
TOKEN_BLACKLIST(jti)   ← logout
```
* **PKs:** UUID hex strings; composite PKs on `likes` and `follows` (this *is* the duplicate-prevention rule).
* **FKs:** `ON DELETE CASCADE` for owned data (deleting a skill removes its sessions/goals/milestones); `SET NULL` for post→skill/file so posts survive.
* **Indexes:** `skills(user_id)`, `practice_sessions(user_id, practiced_at)`, `posts(created_at DESC)`, `comments(post_id)`, `follows(following_id)`.
* **Query patterns:** "my skills", "my sessions by date range", "latest posts", "comments of post", "followers of user".
* **Relational vs NoSQL:** relational fits joins/aggregates (analytics, feed joins). Firestore/DynamoDB scale writes easily but you must denormalize (store username/like_count in the post) and do analytics elsewhere. Full DDL: `cloud/database_service.py`.
* Not built (optional): `notifications`, `blocks` tables – described in design only.

## Object storage
DB stores **metadata + storage reference**; storage stores **bytes**.
```
users/<user_id>/profile/<file_id>.jpg
users/<user_id>/skill/<file_id>.png
users/<user_id>/post/<file_id>.png
users/<user_id>/certificate/<file_id>.pdf
```
Functions: `upload_file`, `get_file`, `delete_file` (`cloud/storage_service.py`). **Permissions:** bucket is private; the API gives short-lived **signed URLs** (S3 presigned URL, or our JWT-signed `/api/files/content/<token>` locally). Public buckets would let anyone enumerate uploads.

## Progress calculation
`progress% = min(100, current/target × 100)` (18/30 h → 60%). Practice logging adds minutes to every ACTIVE goal of that skill whose unit is hours/minutes/sessions; milestones with `target ≤ current` are stamped `achieved_at`; goal becomes COMPLETED at 100%.

## REST API
All routes except register/login/health/`files/content` require `Authorization: Bearer <JWT>`. Errors are JSON `{"detail": "..."}`.

| Method & path | Body / query | Success | Errors |
|---|---|---|---|
| POST /api/register | name, username, email, password | 201 | 409 duplicate, 422 invalid, 429 |
| POST /api/login | email, password | 200 `{access_token}` | 401, 429 |
| POST /api/logout | – | 200 (token revoked) | 401 |
| GET/PUT /api/profile | name, bio, interests, is_public, profile_picture_file_id | 200 | 400 bad file, 401 |
| GET /api/users/{username} | – | 200 public data only | 404 |
| POST /api/skills | skill_name, category, levels, dates, status, description | 201 | 422 |
| GET /api/skills | ?status= | 200 list (own only) | 401 |
| GET/PUT/DELETE /api/skills/{id} | partial update | 200 | 404 (also if not yours) |
| POST /api/practice | skill_id, duration_minutes, activity, notes, practiced_at | 201 + milestones achieved | 404, 422 |
| GET /api/practice, GET /api/skills/{id}/practice | ?skill_id,limit,offset | 200 | 404 |
| POST /api/goals, GET /api/goals, PUT /api/goals/{id} | skill_id,title,target_value,unit,deadline,milestones | 201/200 (with progress_pct, milestones) | 404, 422 |
| POST /api/posts | content, skill_id?, milestone_id?, file_id? | 201 | 400, 404 |
| GET /api/feed | category,q,sort=recent\|liked,following,limit,offset | 200 | 401 |
| DELETE /api/posts/{id} | – | 200 | 403 not owner, 404 |
| POST/DELETE /api/posts/{id}/like | – | 200 `{liked, like_count}` (idempotent) | 404 |
| POST/GET /api/posts/{id}/comments | content | 201/200 | 404 |
| DELETE /api/comments/{id} | – | 200 | 403, 404 |
| POST /api/posts/{id}/report | reason | 201 | 404 |
| POST/DELETE /api/users/{u}/follow, GET …/followers, …/following | – | 200 | 400 self-follow, 404 |
| POST /api/files/upload | multipart `file`, `purpose` | 201 `{file_id,url}` | 413 size, 415 type, 503 storage |
| DELETE /api/files/{id} | – | 200 | 404 |
| GET /api/analytics/dashboard | – | 200 all analytics | 401 |
| GET /api/community/trending | – | 200 | 401 |
Interactive docs: `http://localhost:8000/docs` (Swagger, auto-generated).

## Architecture
```
Users → Web Frontend (SPA) → REST API (FastAPI, stateless) ─┬→ Auth (JWT verify)
                                                            ├→ Cloud DB (users, skills, goals, posts…)
                                                            ├→ Object Storage (images/files, signed URLs)
                                                            └→ Analytics (SQL + progress_service) → Feed/Dashboard
Advanced: Users → CDN → Frontend(S3) → API Gateway → Lambda/App Runner → RDS + S3 + Redis → CloudWatch
```
Data flow for a post with image: browser uploads file → API validates → object storage → `files` row → browser creates post with `file_id` → feed query joins `files` → API returns signed `media_url` → browser renders `<img>`.

## Folder structure
```
frontend/{index.html, src/{api.js (services), ui.js (utils), app.js (pages), styles.css}}
backend/{app.py, routes/, models/schemas.py, services/, middleware/auth.py, utils/}
cloud/{database_service.py, storage_service.py, auth_service.py}   ← swap point for real cloud services
analytics/progress_service.py     tests/     sample_data/seed.py
docs/  reports/  screenshots/  README.md  requirements.txt  .env.example  .gitignore
```
Note: the frontend is plain JS (Option A) so it runs with zero build step; a React port only needs to reuse `api.js` endpoints.
