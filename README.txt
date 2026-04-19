NyayMarg v2.0 — AI-Powered Indian Legal Analytics & Prediction Platform
========================================================================
Upgraded from JusticeGraph v1.0 (monolithic) to a production-grade modular
FastAPI backend. All code lives in /nyaymarg-backend/.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  API         FastAPI 0.111 + Uvicorn (async, OpenAPI 3.1 at /docs)
  Database    PostgreSQL 15 via SQLAlchemy 2.0 async (asyncpg)
  Auth        JWT (python-jose) + bcrypt (passlib) + role-based access
  ML          Scikit-learn: RandomForestClassifier + LogisticRegression
  NLP         TF-IDF vectorizer + NLTK stop-word pipeline
  Tasks       Celery 5.4 + Redis 7 (broker + result backend)
  Export      ReportLab PDF + Matplotlib dark-theme charts
  Config      pydantic-settings (all env vars in .env.example)
  Logging     structlog (structured JSON)
  Rate limit  slowapi (100 req/min per IP)
  Deploy      Render (render.yaml) + Docker (docker-compose.yml)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA (synthetic, generated on startup)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  df_courts   120 courts across 18 Indian states with backlog risk scores
  df_judges   300 judges with specialisation, rating, reversal rate
  df_cases    7,000 cases with NLP text corpus, outcome labels (binary)
  df_laws     9 major Indian laws (IPC, CPC, IT Act, Constitution, etc.)

  Optional real-data upgrade: DDL Judicial Dataset (81M cases, Open DB
  License). Download CSVs → ./data/ddl_judicial/ → set DDL_ENABLED=True.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ML MODELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  rf_model    RandomForestClassifier — court backlog risk (binary, 7 features)
  lr_model    LogisticRegression + TF-IDF — case outcome (binary, text)
  ensemble    RFC 65% + LR 35% weighted average for case predictions
  similarity  TF-IDF cosine index over 7,000-case corpus for precedent search
  persistence joblib to ./app/ml/artefacts/ (disk-first, train-on-miss)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE MODELS (SQLAlchemy ORM → PostgreSQL tables)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  users             Auth accounts with roles (citizen/lawyer/researcher/admin)
  courts            Mirrors df_courts for relational queries
  judges            Mirrors df_judges
  cases             Mirrors df_cases
  predictions       Logged prediction history per user
  bookmarks         User-saved cases
  notifications     In-app notification log
  chat_messages     Chat session history
  ml_model_versions Model training run metadata + metrics
  datasets          Uploaded file registry with Celery job tracking
  audit_logs        Compliance event log

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTERNAL APIs (all optional, flag-gated in .env)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ECIAPI          FREE, no auth — live eCourts CNR lookup, party search,
                  cause lists (eciapi.akshit.me). ENABLED BY DEFAULT.
  Indian Kanoon   Free non-commercial — 3 crore+ judgments, AI tags,
                  precedent classification (api.indiankanoon.org).
  kanoon.dev      Free tier — structured courts/cases/orders/AI insights.
  SooperKanoon    Free GUID auth — case law search by judge/act/court.
  eCourtsIndia    ₹200 free credits — real-time eCourts scraping, PDF orders,
                  bulk refresh (ecourtsindia.com/api).
  data.gov.in     Free API key — official MoLJ court infrastructure stats,
                  NJDG pendency data, disposal rates.
  CourtListener   Free token — US federal/state opinions, dockets, judges,
                  citation graph (courtlistener.com). For comparative research.
  DDL Dataset     Open DB License — 81M real Indian lower-court cases (bulk
                  download only, no REST API). Replaces synthetic df_cases.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API ENDPOINTS  (base: /api/v1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUTH  /auth
  POST /auth/register          Create new account (email + password + role)
  POST /auth/login             Get JWT access + refresh tokens
  POST /auth/refresh           Rotate access token using refresh token
  GET  /auth/me                Get current user profile
  PUT  /auth/me                Update profile (name, password)

COURTS  /courts
  GET  /courts/                List courts (filter: state, type, risk_category)
  GET  /courts/{id}            Court detail with backlog risk score
  GET  /courts/stats/summary   Aggregate stats: counts by state and risk tier
  GET  /courts/stats/risk-map  All 120 courts with coordinates for map UI
  POST /courts/predict-risk    Run RFC model on custom court feature inputs

JUDGES  /judges
  GET  /judges/                List judges (filter: court, specialisation)
  GET  /judges/{id}            Judge detail with performance metrics
  GET  /judges/leaderboard     Top judges ranked by disposal speed
  GET  /judges/bias-analysis   Judges sorted by bias_index
  GET  /judges/performance     Comparative performance matrix

CASES  /cases
  GET  /cases/                 List cases (paginated, filter: type, status, state)
  GET  /cases/{id}             Case detail
  GET  /cases/search           Keyword search across case_title + case_text
  POST /cases/                 Create new case record
  GET  /cases/stats/summary    Case counts by status, type, state
  GET  /cases/stats/pendency   Pendency distribution (binned days pending)

LAWS  /laws
  GET  /laws/                  List all 9 seed laws
  GET  /laws/{id}              Law detail
  GET  /laws/by-category       Laws grouped by category

PREDICTIONS  /predict
  POST /predict/               Single case outcome prediction (RFC+LR ensemble)
  POST /predict/batch          Batch predictions (up to 50 cases)
  GET  /predict/history        Current user's prediction history
  GET  /predict/{id}/export    Download prediction as PDF report
  DELETE /predict/{id}         Delete a prediction record

ANALYTICS  /analytics
  GET  /analytics/overview     Platform-wide aggregate counts
  GET  /analytics/outcomes     Case outcome distribution (chart data)
  GET  /analytics/case-types   Cases split by type (chart data)
  GET  /analytics/state-heatmap  Case counts per state (18 states)
  GET  /analytics/pendency-trend  Monthly pending-case trend
  GET  /analytics/judge-performance  Judge throughput scatter data
  GET  /analytics/court-risk   Court risk score distribution
  GET  /analytics/model-performance  Live ML model accuracy/AUC metrics
  GET  /analytics/export-pdf   Download full analytics report as PDF

PRECEDENT SEARCH  /similar
  POST /similar/search         Cosine similarity search over 7K-case corpus
  GET  /similar/cases          Browse indexed cases

CHAT  /chat
  POST /chat/message           Send message to intent-aware legal assistant
  GET  /chat/history           Load current session chat history
  DELETE /chat/history         Clear chat session

BOOKMARKS  /bookmarks
  POST /bookmarks/             Bookmark a case
  GET  /bookmarks/             List user bookmarks
  DELETE /bookmarks/{id}       Remove a bookmark

NOTIFICATIONS  /notifications
  GET  /notifications/         List notifications
  GET  /notifications/unread   Unread count
  PUT  /notifications/{id}/read  Mark as read
  DELETE /notifications/{id}   Delete notification

DATASETS  /data
  POST /data/upload            Upload CSV or JSON dataset (triggers Celery task)
  GET  /data/                  List uploaded datasets with job status
  GET  /data/{id}/status       Poll Celery ingestion job status
  DELETE /data/{id}            Delete dataset record

ML MODELS  /model
  GET  /model/active           Current model versions and metrics
  POST /model/train            Trigger background model retrain (Celery)
  GET  /model/job/{task_id}    Poll training job progress (0-100%)
  GET  /model/feature-importance  RFC feature importance weights

USERS (admin)  /users
  GET  /users/                 List all users (admin only)
  GET  /users/{id}             Get user by ID
  PUT  /users/{id}/role        Change user role
  PUT  /users/{id}/deactivate  Deactivate account

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTERNAL API ENDPOINTS  /external
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Indian Kanoon
    GET  /external/ik/search            Full-text search (3 crore+ docs)
    GET  /external/ik/doc/{id}          Full judgment text by doc ID
    GET  /external/ik/fragment/{id}     Highlighted matching excerpt
    GET  /external/ik/meta/{id}         AI tags + structure + precedent labels

  kanoon.dev
    GET  /external/kd/courts            List all Indian courts
    GET  /external/kd/courts/{id}/cases Cases for a specific court
    GET  /external/kd/cases/{id}/orders Case orders with PDF links
    GET  /external/kd/cases/{id}/insights  AI legal insights (habeas etc.)

  SooperKanoon
    GET  /external/sk/search            Search by query/court/judge/act/date
    GET  /external/sk/case              Get case by name

  ECIAPI (FREE, always on)
    GET  /external/eci/case/{cnr}       Live case status by CNR number
    GET  /external/eci/search           Search cases by party name
    GET  /external/eci/causelist        Daily court hearing schedule
    GET  /external/eci/courts           List supported courts

  eCourtsIndia.com
    GET  /external/ecw/case/{cnr}       Real-time case from eCourts.gov.in
    GET  /external/ecw/causelist        Cause list by court + date
    GET  /external/ecw/order/{cnr}/{id} Court order PDF + markdown text
    POST /external/ecw/bulk-refresh     Queue up to 50 CNRs for batch update
    POST /external/ecw/refresh/{cnr}    Force immediate re-scrape (5-10s)
    GET  /external/ecw/enums            Live case type + status codes (free)

  data.gov.in
    GET  /external/gov/infrastructure   Official court infra stats by state
    GET  /external/gov/pendency         NJDG pending case counts
    GET  /external/gov/disposal         District disposal rates by year

  CourtListener (US)
    GET  /external/cl/search            Search US court opinions
    GET  /external/cl/opinion/{id}      Full US opinion text
    GET  /external/cl/docket/{id}       Full US case docket
    GET  /external/cl/judge/{id}        US judge profile + disclosures
    GET  /external/cl/citations/{id}    Citation graph for an opinion

  Aggregated
    GET  /external/search               Fan-out to all enabled APIs, ranked
    POST /external/enrich/{case_id}     Enrich synthetic case with real IK data
    POST /external/import               Import IK cases into similarity index

SYSTEM
  GET  /health    DB + Redis + model status + external API enable flags
  GET  /docs      Swagger UI (OpenAPI 3.1)
  GET  /redoc     ReDoc UI

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACKGROUND TASKS (Celery + Redis)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  train_models_task    Retrain RFC + LR on current corpus (7-step progress)
  process_dataset_task  Validate and ingest uploaded CSV/JSON dataset
  import_ik_cases_task  Fetch IK search results, run NLP, add to cosine index

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTH / ROLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  citizen     Read-only access to courts, cases, predictions
  lawyer      All citizen + create cases, bookmarks, chat
  researcher  All lawyer + datasets, ML model management
  admin       Full access including user management

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  nyaymarg-backend/
  ├── app/
  │   ├── config.py           All settings via pydantic-settings + .env
  │   ├── database.py         Async SQLAlchemy engine + get_db dependency
  │   ├── main.py             FastAPI factory: lifespan, middleware, routers
  │   ├── core/               security.py, exceptions.py, logging.py
  │   ├── data/               seed.py (synthetic data), ddl_loader.py (real)
  │   ├── ml/                 pipeline.py, trainer.py, loader.py, evaluator.py
  │   ├── models/             11 SQLAlchemy ORM models
  │   ├── schemas/            9 Pydantic v2 schema modules
  │   ├── services/           9 service classes (business logic layer)
  │   ├── routers/            15 FastAPI routers
  │   ├── external/           8 external API clients + aggregator
  │   └── tasks/              celery_app.py, training_tasks.py, ingestion_tasks.py
  ├── migrations/env.py       Alembic async migration config (all models imported)
  ├── tests/                  38 tests: unit (seed, ml) + integration (courts, cases, analytics)
  ├── Dockerfile              Non-root image, 4 Uvicorn workers
  ├── docker-compose.yml      API + Worker + PostgreSQL 15 + Redis 7 + Nginx
  ├── render.yaml             Render blueprint (web + worker + managed DB + Redis)
  ├── nginx.conf              Reverse proxy (512MB upload limit)
  ├── requirements.txt        All Python dependencies pinned
  ├── pytest.ini              asyncio_mode = auto
  └── .env.example            All environment variables documented

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPLOY ON RENDER (5 steps)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Push this repo to GitHub.
  2. Go to dashboard.render.com → New → Blueprint.
  3. Connect your repo; Render reads render.yaml automatically.
  4. It will provision: API web service + Celery worker + PostgreSQL + Redis.
  5. Set optional API keys in Render env-var dashboard if you want live data:
       IK_API_TOKEN        → then IK_ENABLED=True
       KANOON_DEV_API_KEY  → then KANOON_DEV_ENABLED=True
       SOOPERKANOON_GUID   → then SOOPERKANOON_ENABLED=True
       DATA_GOV_API_KEY    → then DATA_GOV_ENABLED=True
       ECOURTSINDIA_TOKEN  → then ECOURTSINDIA_ENABLED=True
       COURTLISTENER_TOKEN → then COURTLISTENER_ENABLED=True
     ECIAPI works immediately with no key.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RUN LOCALLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  cd nyaymarg-backend
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env           # fill SECRET_KEY at minimum
  uvicorn app.main:app --reload  # Ensure PostgreSQL is running locally
  # Open http://localhost:8000/docs

  # Full stack with Docker:
  docker-compose up -d
