@echo off
title GemiPersona V20.0
cd /d %~dp0

echo Starting Web Interface...
.venv\Scripts\python.exe -m streamlit run HOME.py

pause