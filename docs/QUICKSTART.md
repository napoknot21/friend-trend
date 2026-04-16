# Quick Start Guide

## 1. Setup
```bash
# Install backend dependencies
pip install -r requirements.txt

# Install Ollama and model
# Visit https://ollama.ai and install
ollama pull mistral

# Install frontend dependencies
cd src/frontend
npm install
cd ../..
```

## 2. Run Everything

### Terminal 1: Process Emails
```bash
$env:PYTHONPATH = "."; python src/backend/src/scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-12-31
```
- Add `--refresh` if you want to rebuild a date range.

### Terminal 2: Start the API
```bash
$env:PYTHONPATH = "."; python src/backend/main.py
```
- API runs at `http://127.0.0.1:8000`.

### Terminal 3: Start the Frontend
```bash
cd src/frontend
npm run dev
```
- Dashboard opens at `http://localhost:5173`.

## 3. Workflow
1. Process emails -> populate the SQLite database.
2. Start the API -> serve the stored data.
3. Open the dashboard -> explore and filter results.

## 4. Useful Commands
```bash
# Process last 30 days
python src/backend/src/scripts/process_emails.py --end-date $(Get-Date -Format "yyyy-MM-dd") --start-date $(Get-Date ("dd/MM/yyyy") -UFormat "%Y-%m-%d")

# Analyze best commentators
python src/backend/src/scripts/analyze_commentators.py

# Refresh specific date range
python src/backend/src/scripts/process_emails.py --start-date 2024-01-01 --end-date 2024-01-31 --refresh
```

## 5. Database
- Default path: `data/trend_classifier.db`
- The DB file is not tracked in Git.
- The `data/` folder and DB file are created automatically when needed.
