# AI Powered Distributed Compute Cloud
## Full Technical Development Plan — All Phases
### Personal GPU/CPU Rental Platform, inspired by AWS EC2 and Vast.ai

## Table of Contents
1. Project Overview
2. Phase 1 — Foundation (Weeks 1-2)
3. Phase 2 — Provider Agent + Resource Monitoring (Weeks 3-4)
4. Phase 3 — Task Allocation, Docker Sandbox Execution, Billing (Weeks 5-7)
5. Phase 4 — Queueing, gRPC, Fault Tolerance (Weeks 8-9)
6. Phase 5 — Observability, Storage Hardening, CI/CD (Weeks 10-11)
7. Phase 6 — AI Scheduler, Kubernetes, Auto-Scaling (Weeks 12-14)
8. Testing Strategy
9. Timeline Summary
10. Resume Bullet

---

## 1. Project Overview
This project builds a two-sided marketplace for compute. Providers rent out idle CPU/GPU/RAM. Renters submit tasks that need compute. The platform matches renters to providers, executes tasks inside sandboxed Docker containers, monitors everything in real time, and bills renters on usage.

The system is built in six phases. Each phase is independently demoable and builds directly on top of the previous one. Do not start a phase before the previous one has a working demo — partial phases compound into an unmanageable system.

### 1.1 Final Technology Stack
| Layer | Technology | Introduced in |
| :--- | :--- | :--- |
| Backend framework | Django + Django REST Framework | Phase 1 |
| Auth | SimpleJWT, django-allauth (Google/GitHub OAuth) | Phase 1 |
| Database | PostgreSQL 15 | Phase 1 |
| Cache / broker | Redis 7 | Phase 1 |
| Background jobs | Celery | Phase 1 |
| Real-time transport | Django Channels (WebSocket) | Phase 2 |
| Containerization | Docker, Docker Compose, docker-py SDK | Phase 1 / 3 |
| Message queue (advanced) | RabbitMQ | Phase 4 |
| RPC | gRPC (protobuf) | Phase 4 |
| Event streaming | Apache Kafka | Phase 5 |
| Object storage | MinIO (S3-compatible) | Phase 3 / 5 |
| Monitoring | Prometheus + Grafana | Phase 5 |
| CI/CD | GitHub Actions | Phase 5 |
| Orchestration | Kubernetes + HPA | Phase 6 |
| Infra as code | Terraform | Phase 6 |
| Secrets management | HashiCorp Vault | Phase 6 |
| AI scheduling | scikit-learn RandomForest / XGBoost | Phase 6 |
| Reverse proxy | NGINX + Gunicorn | Phase 1 |
| Testing | pytest, pytest-django, Locust | All phases |

### 1.2 Repository Structure (target, by end of Phase 3)
```
compute-cloud/
├── backend/
│   ├── config/                # Django settings, asgi.py, wsgi.py, celery.py
│   ├── apps/
│   │   ├── accounts/          # custom User model, JWT, OAuth
│   │   ├── providers/         # ProviderMachine, Heartbeat
│   │   ├── tasks/             # Task, TaskAssignment, scheduler logic
│   │   ├── billing/           # Billing, invoices, payment webhook
│   │   └── executor/          # docker-py sandbox runner
│   ├── requirements.txt
│   └── manage.py
├── agent/                     # provider-side monitoring agent (separate package)
│   ├── agent.py
│   └── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── nginx/
│   └── default.conf
└── .github/workflows/ci.yml
```

---

## 2. Phase 1 — Foundation (Weeks 1-2)
Goal: a working Django + DRF skeleton with authentication, PostgreSQL, Redis, Celery and Docker, all running together via docker-compose.

### 2.1 Environment setup
Already completed:
- Created virtual environment `.venv/`
- Installed dependencies (`django`, `djangorestframework`, `djangorestframework-simplejwt`, `celery`, `redis`, `django-cors-headers`, `psycopg2-binary`, etc.)
- Set up target folder structure under `backend/` and custom apps inside `backend/apps/`.

### 2.2 Custom User model
Django's default User is not extended in place after migrations exist, so define a custom User model before the first migration.
```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
 
class User(AbstractUser):
    class Role(models.TextChoices):
        PROVIDER = 'provider', 'Provider'
        RENTER = 'renter', 'Renter'
        BOTH = 'both', 'Both'
 
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.RENTER)
    oauth_provider = models.CharField(max_length=20, blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```
Set `AUTH_USER_MODEL = "accounts.User"` in settings.py.

### 2.3 JWT authentication
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

Core auth endpoints:
| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| POST | `/api/auth/register/` | Create user, choose role (provider/renter/both) |
| POST | `/api/auth/login/` | Returns access + refresh JWT |
| POST | `/api/auth/refresh/` | Rotate access token |
| POST | `/api/auth/oauth/google/` | Exchange Google id_token for JWT |
| POST | `/api/auth/oauth/github/` | Exchange GitHub code for JWT |
| GET | `/api/auth/me/` | Current user profile |

### 2.4 OAuth (Google & GitHub)
- Install `django-allauth`, add `'allauth.socialaccount.providers.google'` and `'...github'` to `INSTALLED_APPS`.
- Register OAuth app credentials in Google Cloud Console and GitHub Developer Settings, store `CLIENT_ID`/`SECRET` in environment variables.
- Backend exchanges the provider token for user info, creates/fetches the User row, then issues your own JWT pair — the frontend only ever talks to your JWT, not the provider's token.

### 2.5 PostgreSQL + Redis + Celery wiring
Configure Celery and settings accordingly. Ensure Celery tasks run.

### 2.6 docker-compose.yml (Phase 1 baseline)
Version running Postgres, Redis, Celery, and Django.

### 2.7 Phase 1 deliverable checklist
- `docker-compose up` brings up web, celery_worker, db, redis with no manual steps.
- A user can register, log in, receive JWT, hit `/api/auth/me/` and get their profile.
- Google or GitHub login returns a valid JWT pair.
- A test Celery task runs and its result is visible in Redis result backend.

---

*(Details for Phase 2 to Phase 6 are described in detail in the full plan file.)*
