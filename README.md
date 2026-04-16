# Trend is Your Friend

Project to extract market convictions from emails on FX and Equities.

## Project Structure
```text
friend-trend/
|- README.md
|- requirements.txt
|- docs/
|- src/
|  |- backend/
|  |  |- main.py
|  |  \- src/
|  |     |- api/
|  |     |- config/
|  |     |- db/
|  |     |- scripts/
|  |     \- ...
|  \- frontend/
\- data/
   \- trend_classifier.db
```

Notes:
- Backend entrypoint: `src/backend/main.py`
- HTTP/API code: `src/backend/src/api`
- Core backend logic: `src/backend/src`
- Frontend Vue/Vite app: `src/frontend`
- Default SQLite path: `data/trend_classifier.db`
- The DB file is intentionally not tracked in Git

## Setup
1. Install Python dependencies: `pip install -r requirements.txt`
2. Install Ollama if needed and pull a model: `ollama pull mistral`
3. Configure `.env`
4. Install frontend dependencies:
   ```bash
   cd src/frontend
   npm install
   cd ../..
   ```

## Environment
Common local-only setup:

```env
API_HOST=127.0.0.1
API_PORT=8000
VITE_DEV_HOST=127.0.0.1
VITE_DEV_PORT=5173
VITE_API_URL=http://127.0.0.1:8000
SQLITE_DB_PATH=data/trend_classifier.db
```

Important:
- `API_HOST=0.0.0.0` makes the backend listen on all interfaces
- `VITE_API_URL` must be a real reachable IP/host, not `0.0.0.0`
- `SQLITE_DB_PATH` can be relative to project root or absolute on disk

## Usage

### Process Emails
```bash
PYTHONPATH=. python src/backend/src/scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-01-01
```

With refresh:
```bash
PYTHONPATH=. python src/backend/src/scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-01-01 --refresh
```

With strict filtering:
```bash
PYTHONPATH=. python src/backend/src/scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-01-01 --strict
```

### Run the API
```bash
PYTHONPATH=. python src/backend/main.py
```

Dev options:
```bash
PYTHONPATH=. python src/backend/main.py --reload
PYTHONPATH=. python src/backend/main.py --workers 4
```

### Run the Frontend
```bash
cd src/frontend
npm run dev
```

Build:
```bash
npm run build
```

### Maintenance Scripts
```bash
PYTHONPATH=. python src/backend/src/scripts/backfill_missing_views.py
PYTHONPATH=. python src/backend/src/scripts/analyze_commentators.py
PYTHONPATH=. python src/backend/src/scripts/clear_db.py
```

## Database Behavior
- The `data/` directory is created automatically if missing
- The SQLite file is created automatically on first use
- Tables are ensured through SQLAlchemy `create_all`
- `src/backend/src/scripts/migrate_db.py` is only for one-off schema updates on older DB files
