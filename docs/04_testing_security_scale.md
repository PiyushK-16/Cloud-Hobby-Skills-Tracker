# 22–27. Testing, Security, Privacy, Scalability, Analytics, Failure handling

## 22. Test cases
Automated with `pytest` (`tests/test_api.py`). Last run in the build environment: **19 passed** (all 27 IDs below are covered by these tests; rerun on your machine and paste your own output as screenshot #23).

| ID | Scenario | Input | Expected | Actual | P/F |
|---|---|---|---|---|---|
| TC01 | Register | valid data | 201, no password in response | as expected | Pass |
| TC02 | Duplicate registration | same email/username | 409 | as expected | Pass |
| TC03 | Valid login | right creds | 200 + token | as expected | Pass |
| TC04 | Invalid login | wrong password | 401 generic message | as expected | Pass |
| TC05 | Profile update | bio/interests | 200, values saved | as expected | Pass |
| TC06 | Add skill (+invalid level) | good / `GOD` | 201 / 422 | as expected | Pass |
| TC07 | Update skill | status=PAUSED | 200 | as expected | Pass |
| TC08 | Delete skill | id | 200, list empty | as expected | Pass |
| TC09 | Create goal | 20 h, milestones 1,5,20 | 201 | as expected | Pass |
| TC10 | Log practice | 60 min (and 0 min) | 201 / 422 | as expected | Pass |
| TC11 | Progress calc | 1/20 h; 45/30 | 5% ; capped 100% | as expected | Pass |
| TC12 | Milestone completion | reach 1 h, 20 h | milestone achieved; goal COMPLETED | as expected | Pass |
| TC13 | File upload | PNG | 201, signed URL returns same bytes | as expected | Pass |
| TC14 | Invalid file | HTML disguised as `.png` | 415 | as expected | Pass |
| TC15 | Create post | text+skill+image | 201 with media_url | as expected | Pass |
| TC16 | Retrieve feed | filters category/q | correct filtering | as expected | Pass |
| TC17 | Like | B likes A's post | count 1 | as expected | Pass |
| TC18 | Duplicate like | like twice | count stays 1 | as expected | Pass |
| TC19 | Unlike | DELETE like | count 0 | as expected | Pass |
| TC20 | Comment | add + list | visible | as expected | Pass |
| TC21 | Unauthorized delete | A deletes B's comment / B deletes A's post | 403 | as expected | Pass |
| TC22 | Analytics | 2 days × 90 min | 3.0 h, streak 2, top skill | as expected | Pass |
| TC23 | Data isolation | B reads/edits A's skill | 404; email hidden in public API | as expected | Pass |
| TC24 | Storage failure | storage raises | 503 friendly message | as expected | Pass |
| TC25 | Database failure | DB raises | 503 friendly message | as expected | Pass |
| TC26 | Token expiry | expired JWT / no token | 401 "expired" | as expected | Pass |
| TC27 | Logout | use token after logout | 401 | as expected | Pass |
Extra tests: streak math, upload-then-DB-failure cleanup (no orphan object), follow + following feed.
Run: `python -m pytest -v`.

## 23. Security
* **Authentication/passwords:** PBKDF2-HMAC-SHA256, 200k iterations, per-user salt, constant-time compare. Login errors never say which field was wrong.
* **Authorization:** every query filters by `user_id`; foreign ids return 404 (no existence leak); delete post/comment only owner (or admin).
* **HTTPS/encryption:** terminate TLS at the host/CDN (in transit); managed DB/S3 encrypt at rest. Locally HTTP is only for development.
* **Object storage:** private bucket + signed, expiring URLs; keys are server-generated (`users/<id>/<purpose>/<uuid>.<ext>`) – filenames from clients are never used (blocks path traversal).
* **Uploads:** size cap (5 MB), extension/type decided from **magic bytes**, whitelist images (+PDF for certificates), `nosniff` header.
* **Injection:** all SQL uses `?` parameters; dynamic `SET` columns come only from Pydantic schema keys.
* **XSS:** control characters stripped server-side; frontend renders with `textContent` (never `innerHTML`); CSP header.
* **Rate limiting:** in-memory per-IP limiter on login/register (use API Gateway/Redis in production).
* **Secrets:** env vars only; `.env` git-ignored; app refuses to start without `SECRET_KEY`.
* **Logging/monitoring/backup:** server logs errors with stack traces but returns generic messages; `/health`; DB snapshots + bucket versioning in cloud.
* **Why UGC needs more:** strangers' content can carry malware, spam, abuse, or private data, and one bad file/comment is shown to many users → validation, reporting, moderation and rate limits are mandatory.

## 24. Privacy & moderation
Private vs public: `email` and hash never leave `/api/profile` (owner only); public profile exposes name/bio/interests/avatar/counts; `is_public=false` hides everything but username. Sharing is opt-in per post. **Implemented:** report post, delete own content, private profiles. **Designed, not built:** block users, spam scoring, moderation queue for `reports`, image moderation service, account deletion endpoint (cascade deletes make it one `DELETE FROM users` + storage prefix cleanup).

## 25. Scalability
| Scale | Design |
|---|---|
| 10 users | one small instance, SQLite/one DB, local or bucket storage |
| 1,000 | managed PostgreSQL, bucket + CDN, 2 API instances behind LB, indexes, pagination |
| 100,000 | autoscaling stateless API, read replica, Redis cache (feed/trending), background workers/queue for uploads, notifications |
| 1M posts | keyset pagination (not OFFSET), partition/archival, precomputed counters, search index (OpenSearch), feed materialization |
Concepts: horizontal scaling (stateless JWT API ⇒ just add instances), serverless functions for bursty jobs, load balancer, managed DB, object storage + CDN for media, caching, pagination (implemented via `limit/offset`), indexes (implemented), queues + workers for slow work.
**Feed challenge:** "posts from people I follow, newest first" for millions of users.
* *Fan-out on read* (what we do): at request time query posts of followed users. Simple, always fresh, but slow when you follow many users.
* *Fan-out on write*: when someone posts, copy the post id into every follower's precomputed feed. Reads are instant, writes are heavy (celebrity with 1M followers = 1M writes). Real systems mix both.

## 26. Analytics
Implemented in `analytics/progress_service.py` → `GET /api/analytics/dashboard`: total/weekly/monthly hours, most practiced skill, current & longest streak, goals completed/active, milestones, posts, likes & comments received, plus chart series (hours by skill, 8-week trend, 6-month progress, goal completion, skill distribution).

## 27. Failure handling
| Failure | Behavior |
|---|---|
| DB down | `sqlite3.Error` handler → 503 "temporarily unavailable"; transactions roll back; client retries |
| Upload fails | 503 before any DB write; nothing to clean |
| Backend down | frontend shows "Network problem"; data is safe server-side; add health checks + auto-restart |
| Token expired | 401 "Token expired" → frontend clears token and shows login |
| Internet drops | `fetch` error caught → friendly message; user retries (drafts stay in the form) |
| Duplicate request | likes/follows idempotent via PK + `INSERT OR IGNORE`; register race → IntegrityError → 409; for POST practice use an `Idempotency-Key` header (future work) |
| Upload OK, DB write fails | compensating delete of the object (implemented + tested) |
| DB write OK, upload fails | impossible in our order (upload first, then metadata); post creation needs a valid `file_id` |
| Orphans anyway | nightly job lists storage keys absent from `files` and deletes them |
Also: timeouts on outbound calls (S3 client), exponential-backoff retry on the client for 503/429, structured logs with request path.
