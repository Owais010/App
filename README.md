# AdaptIQ — Adaptive Learning Platform
## Live URL = https://adapt--iq.vercel.app/
AI-powered adaptive quiz platform that personalizes difficulty using ML models trained on user performance data.

```
┌─────────────────────────────────────────────────────────────┐
│                        AdaptIQ                              │
│                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Frontend   │───▶│   Backend    │───▶│  ML Service   │    │
│  │ React+Vite │    │ Express+Quiz │    │ FastAPI+ML    │    │
│  │ :5173      │    │ Engine :3000 │    │ :8000         │    │
│  └───────────┘    └──────┬───────┘    └───────┬───────┘    │
│                          │                    │             │
│                          └────────┬───────────┘             │
│                                   ▼                         │
│                            ┌────────────┐                   │
│                            │  Supabase  │                   │
│                            │ (Postgres) │                   │
│                            └────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
App/
├── frontend/          React + Vite UI (port 5173)
├── backend/           Express API + Quiz Engine (port 3000)
├── ml-service/        Python FastAPI + XGBoost/LightGBM (port 8000)
├── sql/migrations/    Supabase database migrations
└── docs/              Technical documentation
```

| Service      | Tech Stack                    | Port | Tests   |
| ------------ | ----------------------------- | ---- | ------- |
| Frontend     | React 18, Vite 5, Tailwind    | 5173 | —       |
| Backend      | Express 4, Supabase JS, Jest  | 3000 | 38 unit |
| ML Service   | FastAPI, XGBoost, LightGBM    | 8000 | 40 unit |

---

## How to Start (Step by Step)

### Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org/))
- **Python** 3.11+ ([download](https://www.python.org/downloads/))
- **Supabase** project ([create free](https://supabase.com/dashboard))
- **Git** ([download](https://git-scm.com/))

### Step 1: Clone and enter the project

```bash
git clone <your-repo-url>
cd App
```

### Step 2: Set up the database

Run these SQL files in your Supabase SQL Editor (Dashboard → SQL Editor → New Query), **in order**:

1. `sql/migrations/001_tables.sql` — Creates 13 core tables
2. `sql/migrations/002_rpc_functions.sql` — Creates 7 atomic RPC functions
3. `sql/migrations/003_indexes.sql` — Adds performance indexes
4. `sql/migrations/004_seed_data.sql` — Seeds subjects, topics, and questions
5. `sql/migrations/005_ml_data_logging.sql` — Adds ML feature tables *(optional)*

### Step 3: Configure environment variables

You need three `.env` files. Get your keys from **Supabase Dashboard → Settings → API**.

**Root `.env`** (used by backend):
```bash
cp .env.example .env
```
```dotenv
# Frontend keys (anon — safe for browser)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...your-anon-key...

# Backend keys (service_role — server-side only, bypasses RLS)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...your-service-role-key...
```

**Frontend `.env`** (copy or symlink from root):
```bash
cp .env frontend/.env
```

**ML Service `.env`**:
```bash
cp ml-service/.env.example ml-service/.env
```
```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...your-service-role-key...
API_KEY=pick_a_secret_key
```

### Step 4: Install dependencies

```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
npm install

# ML Service
cd ../ml-service
python -m venv venv

# Windows:
.\venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### Step 5: Train ML models (first time only)

```bash
cd ml-service
# Make sure venv is activated
python -m training.train_all --rows 10000
```

This generates synthetic training data and trains two models:
- `models/level_classifier.joblib` — XGBoost (99.95% accuracy)
- `models/difficulty_recommender.joblib` — LightGBM (97.45% accuracy)

### Step 6: Start all services

Open three terminals:

**Terminal 1 — ML Service** (start first):
```bash
cd ml-service
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS/Linux
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Backend API**:
```bash
cd backend
npm run dev
```

**Terminal 3 — Frontend**:
```bash
cd frontend
npm run dev
```

### Step 7: Verify everything works

```bash
# ML Service health
curl http://localhost:8000/health
# → {"status":"healthy","models_loaded":{"level_classifier":true,"difficulty_recommender":true}}

# Backend health
curl http://localhost:3000/api/health
# → {"status":"healthy","service":"quiz-engine"}

# Frontend
# Open http://localhost:5173 in your browser
```

---

## Running Tests

```bash
# Backend (38 tests)
cd backend
npm test

# ML Service (40 tests)
cd ml-service
.\venv\Scripts\activate
pytest tests/ -v

# All tests from root
npm run test:backend
npm run test:ml
```

---

## Key Features

### Adaptive Quiz Engine (Backend)
- **3 assessment types**: Diagnostic (broad), Practice (topic-focused), Retest (weak areas)
- **Non-repeating questions**: Questions seen in last 30 days are deprioritized
- **Atomic updates**: PostgreSQL FOR UPDATE locking prevents race conditions
- **Level classification**: Laplace-smoothed accuracy → beginner/intermediate/advanced
- **Personalized recommendations**: Weak topic detection with prioritized study paths

### ML-Powered Difficulty (ML Service)
- **Dual-track inference**: Rules baseline for cold start (<15 answers), ML models for warm users
- **14-dimensional feature vector**: Accuracy, streaks, time patterns, difficulty breakdown
- **60/40 ML blending**: ML predictions blended with static difficulty profiles
- **Zero-downtime fallback**: If ML is offline, quiz engine uses static distributions
- **Real-time adaptation**: Cache invalidation after each quiz updates next predictions

### React Frontend
- **Dark/light theme** with system preference detection
- **Animated transitions** with Framer Motion
- **Performance dashboards** with Recharts radar/bar charts
- **Supabase Auth** integration (email + password)
- **Mobile responsive** with Tailwind CSS

---

## API Quick Reference

### Backend (port 3000)

| Method | Endpoint                  | Auth     | Description              |
| ------ | ------------------------- | -------- | ------------------------ |
| POST   | `/api/start-assessment`   | User ID  | Generate a quiz          |
| POST   | `/api/finish-assessment`  | User ID  | Submit answers & score   |
| POST   | `/api/resume-assessment`  | User ID  | Resume incomplete quiz   |
| GET    | `/api/recommendations`    | User ID  | Get study recommendations|
| GET    | `/api/user/profile`       | User ID  | Get user stats           |
| GET    | `/api/health`             | None     | Health check             |

### ML Service (port 8000)

| Method | Endpoint                   | Auth       | Description                |
| ------ | -------------------------- | ---------- | -------------------------- |
| POST   | `/predict/level`           | X-API-Key  | Predict user level         |
| POST   | `/predict/difficulty`      | X-API-Key  | Recommend difficulty       |
| POST   | `/predict/next-question`   | X-API-Key  | Success prob per difficulty |
| POST   | `/predict/batch`           | X-API-Key  | Multi-topic predictions    |
| POST   | `/cache/invalidate`        | X-API-Key  | Clear feature cache        |
| GET    | `/health`                  | None       | Health check               |
| GET    | `/metrics`                 | X-API-Key  | Prediction stats           |

Full API docs: [ml-service/API_DOCUMENTATION.md](ml-service/API_DOCUMENTATION.md)

---

## Docker (ML Service)

```bash
cd ml-service
docker-compose up --build
```

Requires Docker Desktop running. Models are trained at build time.

---

## Documentation

| Document | Description |
| -------- | ----------- |
| [docs/DEV_QUICKSTART.md](docs/DEV_QUICKSTART.md) | Dev quickstart — run everything locally in ~10 min |
| [docs/DEPLOY_VERCEL.md](docs/DEPLOY_VERCEL.md) | Deploy all 3 services to Vercel |
| [docs/QUIZ_ENGINE.md](docs/QUIZ_ENGINE.md) | Quiz engine technical docs, DB schema, API reference |
| [ml-service/README.md](ml-service/README.md) | ML service setup, API usage, model training |
| [ml-service/API_DOCUMENTATION.md](ml-service/API_DOCUMENTATION.md) | Full ML API reference with request/response examples |

---

## Troubleshooting

| Problem | Solution |
| ------- | -------- |
| `SUPABASE_URL not set` warning | Create `.env` with your Supabase credentials |
| ML service returns `null` predictions | Normal — falls back to rules. Start ML service for ML predictions |
| `ECONNREFUSED :3000` | Start the backend: `cd backend && npm run dev` |
| Docker build fails | Ensure Docker Desktop is running: `docker info` |
| `No questions available` | Run `004_seed_data.sql` migration in Supabase SQL Editor |
| Frontend can't auth | Check `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `frontend/.env` |
| Backend tests fail | Run `cd backend && npm install` first |
| `--experimental-vm-modules` error | Use `npm test` not `npx jest` (the flag is in package.json scripts) |
