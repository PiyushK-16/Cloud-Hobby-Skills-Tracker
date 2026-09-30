# 28, 30, 31. GitHub strategy, 14-day plan, screenshots

## Repository
Name `Cloud-Hobby-Skills-Tracker`. Description: *Cloud-based hobby and skill tracking platform featuring progress analytics, cloud storage, user authentication, goal tracking, community sharing, and scalable social features.*
Topics: `cloud-computing skill-tracker community-platform python fastapi react cloud-storage cloud-database rest-api full-stack authentication analytics` (add `react` only if you port the frontend).
```bash
git init
git add .
git commit -m "Initialize cloud hobby and skills tracker"
git branch -M main
git remote add origin <repository-url>
git push -u origin main
```
Before first push run `git status` and confirm `.env`, `data/`, `uploads/` are NOT listed. Don't upload the whole finished project in one commit: follow the day-by-day commits below (`git add <files>; git commit -m "…"`) so history shows real progress. Only claim what you actually did each day.

CI (`.github/workflows/ci.yml`):
```yaml
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python -m pytest -q
```

## 14-day plan
| Day | Work / files | Commit message | Screenshot → proves |
|---|---|---|---|
| 1 | folders, README stub, `docs/`, architecture diagram | "Create cloud application architecture" | folder tree + diagram → planning |
| 2 | `cloud/auth_service.py`, `routes/auth.py`, `middleware/auth.py` | "Implement user authentication" | Swagger register/login → auth works |
| 3 | `routes/profile.py`, schemas | "Add user profile management" | profile page/API → user data |
| 4 | `routes/skills.py` | "Implement hobby and skill tracking" | skills dashboard → CRUD |
| 5 | `routes/practice.py` (sessions), `tracking_service.py` | "Add practice session tracking" | session entry + progress → business logic |
| 6 | goals/milestones, `progress_service.py` | "Implement goals and milestones" | milestone achieved → progress math |
| 7 | `cloud/database_service.py` (schema, indexes) | "Integrate cloud database" | DB browser tables → persistence (swap to managed PG here if doing Option B) |
| 8 | `cloud/storage_service.py`, `routes/files.py` | "Add cloud object storage" | bucket/uploads folder + signed URL → object storage |
| 9 | `routes/posts.py`, feed UI | "Build community sharing module" | community feed → UGC |
| 10 | `routes/social.py` | "Implement likes and comments" | likes/comments + second user → interaction |
| 11 | `routes/analytics.py`, dashboard UI | "Add progress analytics dashboard" | charts → analytics |
| 12 | security headers, validation, `tests/` | "Add cloud security controls" / "Add automated tests" | pytest green + isolation test → quality |
| 13 | deploy, env vars | "Deploy application to cloud" | host dashboard + live URL → cloud deployment |
| 14 | README, report, screenshots | "Complete README and documentation" | GitHub repo/README → documentation |

## Screenshot checklist (save in `screenshots/`)
01_project-folder-structure · 02_cloud-architecture-diagram · 03_registration-page · 04_login-page · 05_user-profile · 06_add-skill-page · 07_skills-dashboard · 08_goal-creation · 09_practice-session-entry · 10_progress-calculation · 11_milestone-achieved · 12_analytics-dashboard · 13_cloud-database · 14_cloud-storage-upload · 15_achievement-image · 16_create-community-post · 17_community-feed · 18_like-interaction · 19_comment-interaction · 20_second-user-account · 21_user-data-isolation-test (curl 404) · 22_rest-api-response (Swagger) · 23_automated-tests-pytest · 24_cloud-deployment-dashboard · 25_live-application · 26_github-commit-history · 27_github-repository · 28_readme-preview (all `.png`).
