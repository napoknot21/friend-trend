# Quick Start Guide

## 1️⃣ Setup (One-time)
```bash
# Install backend dependencies
pip install -r requirements.txt

# Install Ollama and model
# Visit https://ollama.ai and install
ollama pull mistral

# Install frontend dependencies
cd frontend
npm install
cd ..
```

## 2️⃣ Run Everything (3 terminals)

### Terminal 1: Process Emails (Backend)
```bash
$env:PYTHONPATH = "."; python scripts/process_emails.py --start-date 2023-01-01 --end-date 2024-12-31
```
- Or with refresh: add `--refresh` flag
- Wait for completion, then data is in DB

### Terminal 2: Start API Server (Backend)
```bash
$env:PYTHONPATH = "."; python api/main.py
```
- API runs at http://127.0.0.1:8000
- Keep this running for frontend to work

### Terminal 3: Start Frontend (Dev Server)
```bash
cd frontend
npm run dev
```
- Dashboard opens at http://localhost:5173
- Automatically fetches from API

## 🎯 Features
- **Filters**: Underlying, Bank, Sentiment, Date Range
- **Charts**: Sentiment Distribution, Confidence Distribution
- **Table**: All views with sortable data
- **Stats**: Total views, bullish/bearish/neutral counts

## 🔄 Workflow
1. Process emails → populates DB
2. Start API → serves data
3. Open Dashboard → visualize & filter

## 📊 Example Commands
```bash
# Process last 30 days
python scripts/process_emails.py --end-date $(Get-Date -Format "yyyy-MM-dd") --start-date $(Get-Date ("dd/MM/yyyy") -UFormat "%Y-%m-%d")

# Analyze best commentators
python scripts/analyze_commentators.py

# Refresh specific date range (delete and re-analyze)
python scripts/process_emails.py --start-date 2024-01-01 --end-date 2024-01-31 --refresh
```
