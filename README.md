# Smart Job Application Tracker & AI Interview Prep Assistant

This project is a web-based application designed to streamline job tracking and provide AI-powered interview preparation.

## Tech Stack
- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **Database**: SQLite (local dev), PostgreSQL (production)
- **AI**: OpenAI API
- **Integrations**: Gmail API, Google Calendar API

## Architecture
- `backend/`: FastAPI application handling logic, database connections, and external API integrations.
- `frontend/`: Streamlit application serving as the user interface.

## Local Setup (Quick Start)

### 1. Prerequisites
- Python 3.8 or higher installed.

### 2. Installation
Open a terminal in the project root:

```bash
# Install Backend Dependencies
pip install -r backend/requirements.txt

# Install Frontend Dependencies
pip install -r frontend/requirements.txt
```

### 3. Running the App

You need two separate terminal windows.

**Terminal 1 (Backend):**
```bash
uvicorn backend.app.main:app --reload
```
*The API will start at http://localhost:8000*

**Terminal 2 (Frontend):**
```bash
streamlit run frontend/app.py
```
*The UI will open in your browser at http://localhost:8501*

## Docker Setup (Optional - for PostgreSQL)
If you want to use PostgreSQL instead of SQLite:
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Run `docker-compose up -d` to start the database.
3. Update `backend/app/core/config.py` to use the PostgreSQL URL.
