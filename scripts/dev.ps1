# 一键启动后端开发服务器（PowerShell）
# 用法：在仓库根目录执行  .\scripts\dev.ps1
# 前端请另开一个终端，在 frontend/ 下执行 npm run dev

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $root "backend"

if (-not (Test-Path (Join-Path $backend ".venv"))) {
    Write-Host "未找到 backend/.venv，请先按 README「快速开始」创建虚拟环境：" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor Yellow
    Write-Host "  py -3.13 -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 切换到 backend 目录：app.core.config 的 env_file=".env" 是相对当前工作目录解析的
Set-Location $backend

if (-not (Test-Path ".env")) {
    Write-Host "未找到 backend/.env，已提示先复制模板：" -ForegroundColor Yellow
    Write-Host "  Copy-Item .env.example .env" -ForegroundColor Yellow
    Write-Host "（未配置也能启动，AI 会降级为规则版建议）" -ForegroundColor Yellow
}

Write-Host "启动后端：http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "健康检查：http://127.0.0.1:8000/api/health" -ForegroundColor Green
Write-Host "接口文档：http://127.0.0.1:8000/docs" -ForegroundColor Green

& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
