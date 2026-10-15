<#
.SYNOPSIS
    Automated Sales Data Engineering Pipeline - Task Runner for Windows PowerShell.

.DESCRIPTION
    Convenient CLI task runner to execute pipeline tasks, tests, analytics, and cleanup.

.EXAMPLE
    .\run.ps1 test
    .\run.ps1 coverage
    .\run.ps1 run
    .\run.ps1 run-clean
    .\run.ps1 analytics
    .\run.ps1 clean
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("test", "coverage", "run", "run-clean", "analytics", "clean", "help")]
    [string]$Task = "help"
)

$ErrorActionPreference = "Stop"

switch ($Task) {
    "test" {
        Write-Host ">>> Running automated test suite with pytest..." -ForegroundColor Cyan
        python -m pytest tests/ -v
    }

    "coverage" {
        Write-Host ">>> Running test suite with coverage report..." -ForegroundColor Cyan
        python -m pytest --cov=src --cov=main tests/ -v
    }

    "run" {
        Write-Host ">>> Executing pipeline on sample data (with intentional anomalies)..." -ForegroundColor Cyan
        python main.py
    }

    "run-clean" {
        Write-Host ">>> Executing pipeline on 100% clean baseline dataset..." -ForegroundColor Cyan
        python main.py -i data/raw/sales_clean_batch.csv
    }

    "analytics" {
        Write-Host ">>> Running SQL Analytics against warehouse..." -ForegroundColor Cyan
        python run_analytics.py
    }

    "clean" {
        Write-Host ">>> Cleaning cache artifacts and temporary exports..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Include __pycache__, .pytest_cache -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include .coverage, *.pyc -Recurse -File | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "Cleanup completed." -ForegroundColor Green
    }

    "help" {
        Write-Host "`nSales Data Engineering Pipeline - Task Runner" -ForegroundColor Green
        Write-Host "Usage: .\run.ps1 [task]`n"
        Write-Host "Available Tasks:"
        Write-Host "  test       - Run all 26 pytest unit and integration tests"
        Write-Host "  coverage   - Run tests with code coverage percentage"
        Write-Host "  run        - Execute pipeline on sample data (quarantine demonstration)"
        Write-Host "  run-clean  - Execute pipeline on 100% clean baseline data"
        Write-Host "  analytics  - Print full SQL business intelligence analytics report"
        Write-Host "  clean      - Remove temporary bytecode, coverage, and cache files"
        Write-Host ""
    }
}
