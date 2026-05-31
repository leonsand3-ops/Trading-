@echo off
echo Starting Trading Signal Platform...
echo.

cd backend
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r ..\backend\requirements.txt
cd ..

echo Starting backend on http://localhost:8000
start "Backend" cmd /k "call backend\.venv\Scripts\activate.bat && uvicorn backend.main:app --reload --port 8000"

cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
)
echo Starting frontend on http://localhost:5173
start "Frontend" cmd /k "npm run dev"
cd ..

echo.
echo Platform running:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API docs: http://localhost:8000/docs
echo.
pause
