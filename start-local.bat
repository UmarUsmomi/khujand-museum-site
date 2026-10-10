@echo off
title Khujand Museum Local Server
echo ============================================================
echo   Khujand Museum Website - Local Development Server
echo ============================================================
echo Starting server on http://localhost:3000 ...
start http://localhost:3000
python -m http.server 3000
pause
