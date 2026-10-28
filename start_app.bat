@echo off
set OLLAMA_MODELS=D:\ollama_models
echo ============================================================
echo   FailureForensicsTool Launcher
echo   Model Storage: D:\ollama_models
echo   GPU Engine: NVIDIA GeForce RTX 4050
echo ============================================================
echo.
echo Select interface:
echo [1] Modern Web Application (HTML5 / CSS3 / Vanilla JS) [Recommended]
echo [2] Legacy Streamlit Dashboard
echo.
set /p choice="Choose an option (1 or 2, default 1): "
if "%choice%"=="2" (
    echo Launching Streamlit at http://localhost:8501...
    .\.venv\Scripts\python.exe -m streamlit run app.py
) else (
    echo Launching Modern Web UI at http://localhost:8000...
    start http://localhost:8000
    .\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
)
pause
