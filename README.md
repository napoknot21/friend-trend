# Trend is Your Friend

Project to extract market convictions from emails on FX and Equities.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up Ollama: Install Ollama, run `ollama pull mistral`
3. Configure `.env` with any needed vars.

### Network / Host Config
The project now reads host and port settings from the root `.env`.

Common local-only setup:
```env
API_HOST=127.0.0.1
API_PORT=8000
VITE_DEV_HOST=127.0.0.1
VITE_DEV_PORT=5173
VITE_API_URL=http://127.0.0.1:8000
```

Example LAN exposure:
```env
API_HOST=0.0.0.0
API_PORT=8000
VITE_DEV_HOST=0.0.0.0
VITE_DEV_PORT=5173
VITE_API_URL=http://192.168.1.42:8000
```

Important:
- `API_HOST=0.0.0.0` tells the backend to listen on all interfaces.
- `VITE_API_URL` must use the real IP address your browser can reach, not `0.0.0.0`.

## Usage

### Backend - Process Emails
- **Basic Run** (process emails for a date range):
  ```
  PYTHONPATH=. python scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-01-01
  ```
  - This reads emails from Outlook, filters with classifier, batches to LLM, stores in DB.

- **Refresh Mode** (re-process and update existing data):
  ```
  PYTHONPATH=. python scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-01-01 --refresh
  ```
  - Deletes old data for the range, then re-runs.

- **Strict filtering mode**:
  ```
  PYTHONPATH=. python scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-01-01 --strict
  ```
  - Apply stronger criteria to market commentary filtering.

- **Clear the database**:
  ```
  PYTHONPATH=. python scripts/clear_db.py
  ```
  - Removes all rows from `emails` and `underlying_views` while keeping the schema.

- **Analyze Commentators**:
  ```
  PYTHONPATH=. python scripts/analyze_commentators.py
  ```
  - Ranks banks by views and confidence.

### Backend - API Server
- Start the API from project root:
  ```
  python api/main.py
  ```
  - Uses `.env` defaults for `API_HOST`, `API_PORT`, `API_RELOAD`, and `API_WORKERS`
  - Example with `.env`: `http://127.0.0.1:8000` or your LAN IP if exposed
  - Supports development options:
    - `python api/main.py --reload`
    - `python api/main.py --workers 4`
  - Endpoints:
    - `GET /views` to read DB content
    - `POST /process` to fetch and analyze new emails for a range

### Frontend - Dashboard
1. **Install Frontend Dependencies**:
   ```
   cd frontend
   npm install
   ```

2. **Run Frontend Dev Server**:
   ```
   npm run dev
   ```
   - Uses `.env` defaults for `VITE_DEV_HOST`, `VITE_DEV_PORT`, `VITE_DEV_OPEN`
   - Frontend connects to the backend using `VITE_API_URL`

3. **Build for Production**:
   ```
   npm run build
   ```

## Flow
1. Read emails from Outlook.
2. Filter with score-based classifier.
3. Batch send filtered emails to local LLM for extraction.
4. Store in DB.
5. API serves filtered data.
6. Frontend displays charts, tables, and filters.
