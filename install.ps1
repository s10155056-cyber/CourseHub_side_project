#!/usr/bin/env pwsh

#Requires -RunAsAdministrator

<#
.SYNOPSIS
CourseHub RAG + LLM 系統 - 自動安裝腳本

.DESCRIPTION
自動檢查和安裝所有必需的依賴：
- Ollama (本地 LLM 框架)
- Mistral 7B 模型 (4GB)
- Python 依賴包 (requests, streamlit)

.EXAMPLE
./install.ps1

#>

$ErrorActionPreference = "Continue"

# 顏色定義
$colors = @{
    Success = "Green"
    Error   = "Red"
    Warning = "Yellow"
    Info    = "Cyan"
    Muted   = "Gray"
}

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet("Success", "Error", "Warning", "Info", "Muted")]
        [string]$Type = "Info"
    )
    
    $emoji = @{
        Success = "✅"
        Error   = "❌"
        Warning = "⚠️"
        Info    = "ℹ️"
        Muted   = "  "
    }
    
    Write-Host "$($emoji[$Type]) $Message" -ForegroundColor $colors[$Type]
}

function Separator {
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
}

# 標題
Clear-Host
Separator
Write-Host "🚀 CourseHub RAG + LLM 系統 - 自動安裝向導" -ForegroundColor Cyan
Separator
Write-Host ""

# 第 1 步：檢查 Python
Write-Status "第 1 步：檢查 Python" Info
Separator

try {
    $pythonVersion = & python --version 2>&1
    Write-Status "Python 已安裝: $pythonVersion" Success
} catch {
    Write-Status "Python 未安裝" Error
    Write-Host ""
    Write-Host "📥 請先安裝 Python 3.9+"
    Write-Host "   訪問: https://www.python.org"
    Write-Host "   下載 Python 3.11 或更高版本"
    Write-Host ""
    Write-Host "⚠️  安裝時記得勾選『Add Python to PATH』"
    Write-Host ""
    Read-Host "按 Enter 打開 Python 官網"
    Start-Process "https://www.python.org"
    exit 1
}

Write-Host ""

# 第 2 步：檢查/安裝 Ollama
Write-Status "第 2 步：檢查 Ollama" Info
Separator

$ollamaExists = $null
try {
    $ollamaExists = & ollama --version 2>&1
    Write-Status "Ollama 已安裝: $ollamaExists" Success
} catch {
    Write-Status "Ollama 未安裝" Warning
    Write-Host ""
    Write-Host "📥 Ollama 是運行本地 LLM 的關鍵"
    Write-Host "   訪問: https://ollama.ai"
    Write-Host "   下載: OllamaSetup.exe (約 200MB)"
    Write-Host ""
    Write-Host "📋 安裝步驟:"
    Write-Host "   1. 雙擊 OllamaSetup.exe"
    Write-Host "   2. 選擇默認選項"
    Write-Host "   3. 安裝完成後重新運行此腳本"
    Write-Host ""
    $response = Read-Host "已安裝 Ollama 嗎? (y/n)"
    if ($response -ne "y") {
        Read-Host "按 Enter 打開 Ollama 官網"
        Start-Process "https://ollama.ai"
        exit 1
    }
}

Write-Host ""

# 第 3 步：檢查/下載 Mistral 模型
Write-Status "第 3 步：檢查 Mistral 7B 模型" Info
Separator

Write-Host "檢查已安裝的模型..." -ForegroundColor Gray

try {
    $models = & ollama list 2>&1
    
    if ($models -match "mistral") {
        Write-Status "Mistral 模型已下載" Success
    } else {
        Write-Status "Mistral 模型未下載" Warning
        Write-Host ""
        Write-Host "📥 正在下載 Mistral 7B 模型 (~4GB)..."
        Write-Host "⏳ 這可能需要 5-15 分鐘，取決於網速"
        Write-Host "🔄 請耐心等待..."
        Write-Host ""
        
        & ollama pull mistral
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Mistral 下載完成" Success
        } else {
            Write-Status "Mistral 下載失敗" Error
            Write-Host ""
            Write-Host "請檢查："
            Write-Host "1. 網絡連接是否正常"
            Write-Host "2. Ollama 服務是否正在運行 (ollama serve)"
            Write-Host "3. 硬盤空間是否充足 (需要 ~5GB)"
            exit 1
        }
    }
} catch {
    Write-Status "檢查模型失敗" Error
    Write-Host "確保 Ollama 已啟動: ollama serve"
    exit 1
}

Write-Host ""

# 第 4 步：升級 pip
Write-Status "第 4 步：升級 Python 包管理器" Info
Separator

Write-Host "正在升級 pip..." -ForegroundColor Gray
& python -m pip install --upgrade pip -q
Write-Status "pip 升級完成" Success

Write-Host ""

# 第 5 步：安裝 Python 依賴
Write-Status "第 5 步：安裝 Python 依賴" Info
Separator

Write-Host "正在安裝 requests..." -ForegroundColor Gray
& pip install requests -q
if ($LASTEXITCODE -eq 0) {
    Write-Status "requests 已安裝" Success
} else {
    Write-Status "requests 安裝失敗" Error
}

Write-Host "正在安裝 streamlit..." -ForegroundColor Gray
& pip install streamlit -q
if ($LASTEXITCODE -eq 0) {
    Write-Status "streamlit 已安裝" Success
} else {
    Write-Status "streamlit 安裝失敗" Error
}

Write-Host ""

# 第 6 步：驗證安裝
Write-Status "第 6 步：驗證安裝" Info
Separator

Write-Host "驗證 Python 包..." -ForegroundColor Gray
& python -c "import requests; print('✅ requests')" 2>$null
& python -c "import streamlit; print('✅ streamlit')" 2>$null

Write-Host "驗證 Ollama 和模型..." -ForegroundColor Gray
try {
    $models = & ollama list 2>&1
    if ($models -match "mistral") {
        Write-Host "✅ mistral" -ForegroundColor Green
    }
} catch {
    Write-Status "模型檢查失敗" Error
}

Write-Host ""

# 完成
Separator
Write-Status "安裝完成！準備開始使用" Success
Separator

Write-Host ""
Write-Host "🚀 立即啟動 CourseHub：" -ForegroundColor Cyan
Write-Host ""
Write-Host "    cd 'C:\Users\s1015\OneDrive\桌面\CourseHub'" -ForegroundColor White
Write-Host "    streamlit run app_streamlit.py" -ForegroundColor White
Write-Host ""
Write-Host "✨ 瀏覽器將自動打開 http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 首次使用建議：" -ForegroundColor Yellow
Write-Host "   1. 打開 START_HERE.md 了解基本功能" -ForegroundColor White
Write-Host "   2. 試試「智能問答」功能" -ForegroundColor White
Write-Host "   3. 查看「課程推薦」的結果" -ForegroundColor White
Write-Host ""

$response = Read-Host "是否立即啟動系統? (y/n)"

if ($response -eq "y") {
    Set-Location "C:\Users\s1015\OneDrive\桌面\CourseHub"
    Write-Host ""
    Write-Host "⏳ 啟動中..." -ForegroundColor Cyan
    Write-Host ""
    
    & streamlit run app_streamlit.py
} else {
    Write-Host "你可以稍後手動運行以上命令" -ForegroundColor Yellow
}

Read-Host "按 Enter 結束"
