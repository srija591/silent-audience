@echo off
echo === Backend setup ===
cd backend
python -m venv venv || goto :err
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :err
echo Installing optional pitch analysis (ok if this fails)...
pip install -r requirements-optional.txt
if not exist .env copy .env.example .env
cd ..
echo === Frontend setup ===
cd frontend
call npm install || goto :err
cd ..
echo.
echo Setup done. Now double-click run-backend.bat, then run-frontend.bat
pause
exit /b 0
:err
echo Setup failed. Check the message above.
pause
