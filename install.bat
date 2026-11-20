@echo off
REM CourseHub RAG + LLM 系統 - 自動安裝脚本
REM 完全自動化安裝所有依賴

setlocal enabledelayedexpansion

cls
echo ════════════════════════════════════════════════════════════
echo 🚀 CourseHub RAG + LLM 系統 - 自動安裝向導
echo ════════════════════════════════════════════════════════════
echo.

REM 檢查管理員權限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  需要管理員權限運行此腳本
    echo 請右鍵點擊此文件 → 選擇「以管理員身份運行」
    pause
    exit /b 1
)

echo ✅ 已獲得管理員權限
echo.

REM 第 1 步：檢查 Python
echo ════════════════════════════════════════════════════════════
echo 📍 第 1 步：檢查 Python
echo ════════════════════════════════════════════════════════════
python --version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Python 已安裝
    python --version
) else (
    echo ❌ Python 未安裝
    echo 請先從 https://www.python.org 下載並安裝 Python 3.9+
    pause
    exit /b 1
)
echo.

REM 第 2 步：檢查和安裝 Ollama
echo ════════════════════════════════════════════════════════════
echo 📍 第 2 步：檢查/安裝 Ollama
echo ════════════════════════════════════════════════════════════

ollama --version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Ollama 已安裝
    ollama --version
) else (
    echo ⚠️  Ollama 未安裝
    echo 正在下載 OllamaSetup.exe...
    echo.
    echo 📥 一旦下載完成，請：
    echo    1. 雙擊 OllamaSetup.exe
    echo    2. 選擇默認選項並安裝
    echo    3. 安裝完成後重新運行此腳本
    echo.
    echo 🔗 如果沒有自動下載，請手動訪問：
    echo    https://ollama.ai
    echo.
    pause
)
echo.

REM 第 3 步：下載 Mistral 模型
echo ════════════════════════════════════════════════════════════
echo 📍 第 3 步：下載 Mistral 模型 (可能需要 5-10 分鐘)
echo ════════════════════════════════════════════════════════════

ollama list | findstr mistral >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Mistral 模型已下載
) else (
    echo ⏳ 正在下載 Mistral 模型 (~4GB)...
    echo 這可能需要 5-15 分鐘，取決於你的網速
    echo.
    ollama pull mistral
    if %errorLevel% equ 0 (
        echo ✅ Mistral 模型下載完成
    ) else (
        echo ❌ 下載失敗
        echo 請檢查網絡連接並重試
        pause
        exit /b 1
    )
)
echo.

REM 第 4 步：安裝 Python 依賴
echo ════════════════════════════════════════════════════════════
echo 📍 第 4 步：安裝 Python 依賴
echo ════════════════════════════════════════════════════════════

python -m pip install --upgrade pip >nul 2>&1
echo 正在安裝 requests...
pip install requests -q
echo 正在安裝 streamlit...
pip install streamlit -q
echo ✅ Python 依賴安裝完成
echo.

REM 第 5 步：驗證安裝
echo ════════════════════════════════════════════════════════════
echo 📍 第 5 步：驗證安裝
echo ════════════════════════════════════════════════════════════
echo.

python -c "import requests; print('✅ requests 已安裝')" 2>nul || echo "❌ requests 未安裝"
python -c "import streamlit; print('✅ streamlit 已安裝')" 2>nul || echo "❌ streamlit 未安裝"
ollama list | findstr mistral >nul && echo "✅ Mistral 已安裝" || echo "❌ Mistral 未安裝"
echo.

REM 完成
echo ════════════════════════════════════════════════════════════
echo ✅ 安裝完成！
echo ════════════════════════════════════════════════════════════
echo.
echo 🚀 現在可以啟動系統了！
echo.
echo 運行以下命令啟動 CourseHub：
echo.
echo    cd "C:\Users\s1015\OneDrive\桌面\CourseHub"
echo    streamlit run app_streamlit.py
echo.
echo 瀏覽器將自動打開 http://localhost:8501
echo.
pause
