@echo off
echo Ensuring PostgreSQL container is running...
docker compose up postgres -d

echo Starting Python Backend Dev Server...
cd backend
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
