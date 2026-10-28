param (
    [string]$Mode = "web"
)

# FailureForensicsTool Launcher
# Sets storage path to D:\ollama_models and starts the Modern Web App (HTML/CSS/JS) or Streamlit

$env:OLLAMA_MODELS = "D:\ollama_models"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  FailureForensicsTool Launcher" -ForegroundColor Cyan
Write-Host "  Model Storage: D:\ollama_models" -ForegroundColor Yellow
Write-Host "  GPU Engine: NVIDIA GeForce RTX 4050" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# Check if Ollama is running
$ollamaRunning = $false
try {
    $res = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    $ollamaRunning = $true
} catch {
    $ollamaRunning = $false
}

if (-not $ollamaRunning) {
    Write-Host "Starting Ollama server with D:\ollama_models..." -ForegroundColor Green
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "Ollama server is active and ready." -ForegroundColor Green
}

if ($Mode -eq "streamlit") {
    Write-Host "Launching Streamlit UI at http://localhost:8501..." -ForegroundColor Green
    & ".\.venv\Scripts\python.exe" -m streamlit run app.py
} else {
    Write-Host "Launching Advanced Web UI (HTML5/CSS3/JS) at http://localhost:8000..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000"
    & ".\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8000
}
