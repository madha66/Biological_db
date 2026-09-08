# Installation and Setup Guide

This guide walks you through setting up KEGGPathRank locally on Windows, macOS, or Linux.

---

## Prerequisites

- **Python**: Version 3.11 or higher
- **Node.js**: Version 18.0.0 or higher (with `npm`)
- **Git**: For cloning and version control
- **Internet Access**: Required for fetching KEGG REST API data on initial runs (cached afterwards)

---

## Step 1: Clone Repository

```bash
git clone https://github.com/your-username/KEGGPathRank.git
cd KEGGPathRank
```

---

## Step 2: Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (optional):
   ```bash
   # Copy sample configuration
   cp ../.env.example .env
   ```

---

## Step 3: Frontend Setup (React + Vite)

1. Open a separate terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js packages:
   ```bash
   npm install
   ```

---

## Step 4: Running the Application

### Option A: Running Backend and Frontend Separately

**Terminal 1 (Backend):**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
API will be live at `http://localhost:8000`. Swagger interactive docs at `http://localhost:8000/docs`.

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
Web dashboard will be live at `http://localhost:5173`.

---

## Step 5: Verification & Tests

Run the complete backend test suite:
```bash
# Windows
$env:PYTHONPATH = "backend"; python -m pytest backend/tests/ -v

# macOS / Linux
PYTHONPATH=backend pytest backend/tests/ -v
```

---

## Generating Offline Publication Charts

To generate static publication-ready charts using Matplotlib without starting the server:
```bash
python scripts/generate_static_chart.py --demo --output publication_chart.png
```
