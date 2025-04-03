
@echo off
cd /d H:\Pictures\bot-ob
call H:\Pictures\bot-ob\venv\Scripts\activate
call H:\Pictures\bot-ob\venv\Scripts\python.exe -m streamlit run deriv_bot_rise_fall.py
pause
