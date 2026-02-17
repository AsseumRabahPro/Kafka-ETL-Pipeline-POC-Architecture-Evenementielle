# Comprehensive Startup Script
# Initializes and runs entire Kafka ETL system

param(
	[switch]$Headless
)

$projectPath = "C:\Users\Asseu\Desktop\Projet Data\project"
cd $projectPath

$venvPython = Join-Path $projectPath ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
	Write-Host "[INFO] .venv not found. Creating virtual environment..." -ForegroundColor Yellow

	$basePython = $null
	$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
	if ($pyLauncher) {
		foreach ($ver in @("3.11", "3.10", "3.12")) {
			& py -$ver -c "import sys" 2>$null
			if ($LASTEXITCODE -eq 0) {
				$basePython = "py -$ver"
				break
			}
		}
	}

	if (-not $basePython) {
		$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
		if ($null -eq $pythonCmd) {
			Write-Host "[ERROR] Python not found in PATH. Please install Python 3.10 or 3.11 and retry." -ForegroundColor Red
			exit 1
		}
		$basePython = "python"
	}

	& $basePython -m venv .venv
}

if (Test-Path $venvPython) {
	$pythonExe = $venvPython
	Write-Host "[INFO] Using virtual environment: $venvPython" -ForegroundColor Green
} else {
	$pythonExe = "python"
	Write-Host "[WARN] .venv not available. Using system Python." -ForegroundColor Yellow
}

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "KAFKA ETL POC - FULL STARTUP SCRIPT"
Write-Host "===========================================" -ForegroundColor Cyan

# Step 1: Start Docker services
Write-Host "`n[STEP 1] Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d
Start-Sleep -Seconds 5

# Step 1b: Install Python dependencies
Write-Host "`n[STEP 1b] Installing Python dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
	Write-Host "[ERROR] Dependency installation failed. Please check your Python environment and retry." -ForegroundColor Red
	exit $LASTEXITCODE
}

# Step 2: Initialize database
Write-Host "`n[STEP 2] Initializing database schema..." -ForegroundColor Yellow
& $pythonExe init_db.py

# Step 2b: Create Kafka topics
Write-Host "`n[STEP 2b] Creating Kafka topics..." -ForegroundColor Yellow
& $pythonExe create_topics.py

# Step 3: Run comprehensive tests
Write-Host "`n[STEP 3] Running infrastructure tests..." -ForegroundColor Yellow
& $pythonExe full_test.py

# Step 4: Launch all components
Write-Host "`n[STEP 4] Starting all components..." -ForegroundColor Yellow
if ($Headless) {
	$logDir = Join-Path $projectPath "logs"
	New-Item -ItemType Directory -Path $logDir -Force | Out-Null

	Write-Host "  - Producer (log: logs\producer.log)" -ForegroundColor Green
	Start-Process -NoNewWindow -FilePath $pythonExe -ArgumentList "producer/producer.py" -WorkingDirectory $projectPath -RedirectStandardOutput (Join-Path $logDir "producer.log") -RedirectStandardError (Join-Path $logDir "producer.err.log")

	Write-Host "  - Worker ETL (log: logs\worker.log)" -ForegroundColor Green
	Start-Process -NoNewWindow -FilePath $pythonExe -ArgumentList "worker_python/worker.py" -WorkingDirectory $projectPath -RedirectStandardOutput (Join-Path $logDir "worker.log") -RedirectStandardError (Join-Path $logDir "worker.err.log")

	Write-Host "  - Order Validator (log: logs\order_validator.log)" -ForegroundColor Green
	Start-Process -NoNewWindow -FilePath $pythonExe -ArgumentList "worker_python/order_validator.py" -WorkingDirectory $projectPath -RedirectStandardOutput (Join-Path $logDir "order_validator.log") -RedirectStandardError (Join-Path $logDir "order_validator.err.log")

	Write-Host "  - Order Fact Builder (log: logs\order_fact_builder.log)" -ForegroundColor Green
	Start-Process -NoNewWindow -FilePath $pythonExe -ArgumentList "worker_python/order_fact_builder.py" -WorkingDirectory $projectPath -RedirectStandardOutput (Join-Path $logDir "order_fact_builder.log") -RedirectStandardError (Join-Path $logDir "order_fact_builder.err.log")

	Write-Host "  - KPI Dashboard (log: logs\kpi_orders.log)" -ForegroundColor Green
	Start-Process -NoNewWindow -FilePath $pythonExe -ArgumentList "kpi_orders.py" -WorkingDirectory $projectPath -RedirectStandardOutput (Join-Path $logDir "kpi_orders.log") -RedirectStandardError (Join-Path $logDir "kpi_orders.err.log")
} else {
	Write-Host "  - Producer (generates 100 events)" -ForegroundColor Green
	Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectPath'; & '$pythonExe' producer/producer.py`"" -WindowStyle Normal

	Write-Host "  - Worker ETL (processes users)" -ForegroundColor Green
	Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectPath'; & '$pythonExe' worker_python/worker.py`"" -WindowStyle Normal

	Write-Host "  - Order Validator (validates orders)" -ForegroundColor Green
	Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectPath'; & '$pythonExe' worker_python/order_validator.py`"" -WindowStyle Normal

	Write-Host "  - Order Fact Builder (builds data warehouse)" -ForegroundColor Green
	Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectPath'; & '$pythonExe' worker_python/order_fact_builder.py`"" -WindowStyle Normal

	Write-Host "  - KPI Dashboard (displays analytics)" -ForegroundColor Green
	Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$projectPath'; & '$pythonExe' kpi_orders.py`"" -WindowStyle Normal
}

Write-Host "`n===========================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] System startup complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
if ($Headless) {
	Write-Host "`nAll components are running in background. Logs in .\logs\*.log`n" -ForegroundColor Cyan
} else {
	Write-Host "`nAll components are running in separate terminals.`nMonitor the output in each window to track processing.`n" -ForegroundColor Cyan
}

# Step 5: Wait for data then run final test
Write-Host "[STEP 5] Waiting for data ingestion before final test..." -ForegroundColor Yellow
& $pythonExe wait_for_data.py

Write-Host "`n[STEP 6] Running end-to-end test..." -ForegroundColor Yellow
& $pythonExe full_test.py
