# Project Report – Online Hobby & Skills Tracker with Community Sharing on Cloud
*(Fill in name, roll number, institution, dates, deployment URL. Add your screenshots.)*

**Abstract.** This project implements a cloud-based web application where users record hobbies and skills, set goals with milestones, log practice sessions, upload proof, and share achievements with a community. A stateless REST API secured by JWT authentication stores structured data in a relational database and files in object storage, and produces progress analytics. The work demonstrates cloud concepts: centralized storage, cross-device access, managed storage, security, scalability and failure handling.

**1. Introduction.** Hobby learners track progress in scattered notes and lack accountability and community. A cloud application centralizes this data and lets it be reached from any device.

**2. Problem statement.** Build a secure, scalable, cloud-oriented platform for tracking skill progress with community sharing, using only synthetic data and free/local services.

**3. Objectives.** User accounts and profiles; skill/goal/milestone/practice tracking; file uploads to object storage; community feed with likes, comments and follows; analytics; security, testing, deployment, documentation.

**4. Existing system.** Notebooks, spreadsheets, single-device habit apps and generic social networks: no unified tracking + community, poor sync or analytics.

**5. Proposed system.** Web app + REST API + database + object storage + analytics + community, described in `docs/02_design.md`.

**6. Industry relevance.** Same architecture is used in LMS/EdTech, fitness apps, employee learning portals, creator communities and portfolio platforms (`docs/01_concepts_and_options.md`).

**7. Cloud computing concepts.** SaaS/PaaS/IaaS mapping, database, object storage, authentication/authorization, REST, serverless/event-driven design (proposed), scalability, CDN, load balancing, caching, secrets, logging, backup, CI/CD – mapped to project locations in `docs/01_concepts_and_options.md`.

**8. Technology stack.** Python 3, FastAPI, Pydantic, PyJWT, SQLite (PostgreSQL-ready SQL), S3-compatible storage via boto3 (local folder in simulation), vanilla JS front end, pytest, GitHub Actions.

**9. System architecture.** Browser → REST API → {database, object storage, analytics}; advanced: CDN, API gateway, serverless/app runner, managed DB, cache, monitoring.

**10. Database design.** 12 tables (users, files, skills, goals, milestones, practice_sessions, posts, comments, likes, follows, reports, token_blacklist) with PK/FK, cascades and indexes; ER diagram in `docs/02_design.md`.

**11. Cloud storage design.** Path convention `users/<id>/<purpose>/<uuid>.<ext>`; DB keeps metadata; private bucket; signed URLs.

**12. Authentication.** PBKDF2-hashed passwords, JWT with expiry, logout via token blacklist, generic login errors, rate limiting.

**13. Hobby & skill tracking.** CRUD with levels BEGINNER/INTERMEDIATE/ADVANCED and statuses ACTIVE/PAUSED/COMPLETED.

**14. Practice tracking.** Sessions update goals, milestones, weekly/monthly totals and streaks.

**15. Goal management.** progress % = min(100, current/target × 100); milestones auto-achieved; goals auto-completed.

**16. Community sharing.** Posts with optional skill and image, filterable feed (category, search, most liked, following), likes (idempotent), comments, follows, reports.

**17. Analytics.** Totals, weekly/monthly hours, trends, streaks, goal/milestone counts, engagement counts.

**18. API design.** 30+ endpoints listed in `docs/02_design.md` with status codes.

**19. Implementation.** Modular layout: routes → services → cloud layer; cloud layer is the swap point for real cloud services.

**20. Testing.** 19 automated tests covering the 27 planned cases (`docs/04_testing_security_scale.md`); all passed in the build environment.

**21. Cloud deployment.** Student route: PaaS host + S3-compatible bucket (+ persistent DB); enterprise route: AWS reference architecture with Azure/GCP equivalents (`docs/03_run_and_deploy.md`). *Record here what you actually deployed.*

**22. Security & 23. Privacy.** Input validation, parameterized SQL, XSS-safe rendering, upload validation, signed URLs, per-user isolation, private profiles, report mechanism.

**24. Scalability.** 10 → 1M-post design, caching, CDN, queues, fan-out on read vs write.

**25. Results.** Working local system: registration → skill → goal → practice → progress → upload → post → like/comment → analytics. Add screenshots and deployment URL.

**26. Advantages.** Central data, multi-device, secure, modular, testable, cloud-portable.
**27. Limitations.** SQLite by default; in-memory rate limiter; plain-JS UI; no email verification, blocking or moderation queue; timezone-naive streaks.
**28. Future scope.** Managed PostgreSQL + managed auth, React UI, Redis cache, notifications, moderation, mobile app, recommendations.
**29. Conclusion.** The project shows how a real application separates identity, data, media and analytics into cloud-friendly components and can grow from a single server to a scalable architecture.
