# 33–34. Resume, LinkedIn, Interview prep
Use only claims that are true for your build (e.g. mention the cloud host/bucket you actually used).

## Resume bullets
* Designed and built a cloud-hosted hobby & skill tracking platform (FastAPI REST API, JWT auth, relational DB, S3-compatible object storage) with 25+ endpoints and per-user data isolation.
* Implemented goal/milestone tracking, streak and progress analytics, and a community feed with likes, comments and follows; secured uploads with magic-byte validation, size limits and signed URLs.
* Wrote 19 automated pytest tests covering auth, authorization, failure handling (DB/storage outages, token expiry) and set up CI + free-tier cloud deployment.

**2-line description:** Cloud-based hobby & skills tracker with community sharing – REST API, JWT authentication, managed-style database and object storage, analytics dashboard and a social feed. Built to demonstrate cloud architecture, security, scalability and failure handling.

**LinkedIn:** *Online Hobby & Skills Tracker with Community Sharing on Cloud* – A full-stack cloud computing project where users log hobbies, set goals, record practice, and share achievements. I designed the architecture (stateless API, relational schema with indexes, private object storage with signed URLs), implemented authentication/authorization, analytics (streaks, weekly/monthly trends) and a community feed, tested it with automated tests, and documented scaling to 100k users (caching, CDN, queues, fan-out strategies). Tech: Python, FastAPI, SQL, JWT, S3-compatible storage, GitHub Actions.

**Skills:** Cloud architecture, REST API design, authentication/authorization, SQL & schema design, object storage, signed URLs, analytics, secure file upload, rate limiting, failure handling, pytest, Git/GitHub, CI/CD, deployment.

## 10 interview Q&A
1. **Explain your project.** It's a cloud-based tracker where users record hobbies and skills, set goals, log practice, and upload proof, then share achievements in a community feed. A browser front end calls a stateless FastAPI REST API; users are authenticated with JWTs; relational data lives in the database; images live in object storage and the DB keeps only references. Analytics such as hours, streaks and trends are computed server-side, so the same data is available from any device.
2. **Why is this a cloud project?** Data and files are hosted centrally and reached over the network, storage and database are separate managed-style services, the API is stateless so it scales horizontally, and configuration/secrets come from the environment as in real cloud deployments.
3. **Why separate database and object storage?** Databases are good for structured, queryable data; large binaries are cheaper and faster in object storage with CDN support. The `files` table stores `storage_key`, type and size; the bytes are in the bucket.
4. **How does authentication and authorization work?** Passwords are salted PBKDF2 hashes. Login returns a signed JWT with expiry and a `jti`; logout blacklists the `jti`. Authorization is enforced in queries by `user_id`, so another user's skill returns 404, and only owners or admins delete posts/comments.
5. **How do you prevent duplicate likes?** `likes` has a composite primary key `(post_id, user_id)` and I use `INSERT OR IGNORE`, so the operation is idempotent even under double-clicks or races.
6. **How are progress and streaks calculated?** Progress is `min(100, current/target×100)`. Logging practice adds time to active goals and marks milestones. Streak counts consecutive distinct practice days ending today or yesterday; longest streak is the longest run in history.
7. **How do you secure file uploads?** 5 MB limit, file type decided by magic bytes instead of the filename, whitelist of image types, server-generated storage keys, private bucket with expiring signed URLs, and `nosniff` headers.
8. **What if the image uploads but the DB write fails?** I upload first, then insert metadata; if the insert fails I delete the object (compensating action) and log it. A periodic cleanup job would catch anything left over. I tested this case.
9. **How would it scale to 100,000 users?** Autoscaled stateless API behind a load balancer, managed PostgreSQL with replicas and indexes, Redis caching for feed/trending, CDN for media, keyset pagination, and queues/workers for slow tasks. For the feed I'd move from fan-out on read to a hybrid with fan-out on write for normal users.
10. **What would you improve / what did you learn?** Move SQLite to managed PostgreSQL, add refresh tokens and an idempotency key for practice logging, moderation tooling and blocking, and observability dashboards. I learned how to design cloud boundaries (API, DB, storage, auth) and to test failure paths, not just the happy path.
