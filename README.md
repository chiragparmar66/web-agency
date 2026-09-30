# Nexus Studio Platform

A real, professional web development business platform engineered for high-touch customer management, bespoke web development project tracking, transparent revision handling, and payment workflows.

---

## 🏛 Architecture Overview

* **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide Icons
* **Backend**: FastAPI (Python 3.11+ / 3.14+), SQLAlchemy 2.0 Async, Pydantic v2
* **Database**: PostgreSQL (Compatible with Supabase / Neon / Render)
* **Auth**: Secure JWT with Role-Based Access Control (`ADMIN`, `DEVELOPER`, `CUSTOMER`)
* **Storage**: Storage Abstraction Layer (Local disk driver for development, Supabase/S3 for production)
* **Payments**: Razorpay Order Creation + HMAC-SHA256 Backend Signature Verification

---

## 🚀 Quickstart Guide

### Prerequisites
* Python 3.11+
* Node.js 18+ & npm
* PostgreSQL (optional for local SQLite testing)

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run FastAPI Server
uvicorn app.main:app --reload --port 8000
```
Backend API Docs: `http://localhost:8000/docs`  
Health Check: `http://localhost:8000/api/v1/health`

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Frontend App: `http://localhost:3000`

---

## 🧪 Testing & Quality Assurance
```bash
# Run backend test suite
cd backend
pytest -v

# Run frontend lint & type checks
cd frontend
npm run lint
npx tsc --noEmit
```
