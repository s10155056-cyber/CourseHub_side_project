#!/usr/bin/env python
"""
CourseHub RAG + LLM 系統 - Python 自動安裝腳本
自動檢查和安裝所有必需依賴
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

# 顏色代碼
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="info"):
    """打印狀態消息"""
    emojis = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    
    colors_map = {
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.CYAN
    }
    
    emoji = emojis.get(status, "•")
    color = colors_map.get(status, Colors.RESET)
    print(f"{emoji} {color}{message}{Colors.RESET}")

def print_separator():
    """打印分隔線"""
    print("=" * 60)

def run_command(cmd, shell=False):
    """運行系統命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_separator()
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 CourseHub RAG + LLM 系統 - 自動安裝向導{Colors.RESET}")
    print_separator()
    print()
    
    # 第 1 步：檢查 Python
    print(f"{Colors.BOLD}📍 第 1 步：檢查 Python{Colors.RESET}")
    print_separator()
    
    version_ok, stdout, stderr = run_command([sys.executable, "--version"])
    if version_ok:
        print_status(f"Python 已安裝: {stdout}", "success")
    else:
        print_status("Python 未安裝", "error")
        print()
        print("❌ 請先從 https://www.python.org 安裝 Python 3.9+")
        sys.exit(1)
    
    print()
    
    # 第 2 步：檢查 Ollama
    print(f"{Colors.BOLD}📍 第 2 步：檢查 Ollama{Colors.RESET}")
    print_separator()
    
    ollama_ok, stdout, stderr = run_command("ollama --version", shell=True)
    if ollama_ok:
        print_status(f"Ollama 已安裝: {stdout}", "success")
    else:
        print_status("Ollama 未安裝", "warning")
        print()
        print("📥 Ollama 是運行本地 LLM 的關鍵")
        print("   訪問: https://ollama.ai")
        print("   下載: OllamaSetup.exe (~200MB)")
        print()
        response = input("已安裝 Ollama 嗎? (y/n): ").lower()
        if response != "y":
            print("打開 Ollama 官網...")
            webbrowser.open("https://ollama.ai")
            sys.exit(1)
    
    print()
    
    # 第 3 步：檢查 Mistral 模型
    print(f"{Colors.BOLD}📍 第 3 步：檢查 Mistral 7B 模型{Colors.RESET}")
    print_separator()
    
    models_ok, stdout, stderr = run_command("ollama list", shell=True)
    if models_ok and "mistral" in stdout.lower():
        print_status("Mistral 模型已下載", "success")
    else:
        print_status("Mistral 模型未下載", "warning")
        print()
        print("📥 正在下載 Mistral 7B 模型 (~4GB)...")
        print("⏳ 這可能需要 5-15 分鐘，取決於網速")
        print("🔄 請耐心等待...")
        print()
        
        success, _, _ = run_command("ollama pull mistral", shell=True)
        
        if success:
            print_status("Mistral 下載完成", "success")
        else:
            print_status("Mistral 下載失敗", "error")
            print()
            print("請檢查：")
            print("1. 網絡連接是否正常")
            print("2. Ollama 服務是否正在運行 (ollama serve)")
            print("3. 硬盤空間是否充足 (需要 ~5GB)")
            sys.exit(1)
    
    print()
    
    # 第 4 步：升級 pip
    print(f"{Colors.BOLD}📍 第 4 步：升級 Python 包管理器{Colors.RESET}")
    print_separator()
    
    print("正在升級 pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    print_status("pip 升級完成", "success")
    
    print()
    
    # 第 5 步：安裝 Python 依賴
    print(f"{Colors.BOLD}📍 第 5 步：安裝 Python 依賴{Colors.RESET}")
    print_separator()
    
    packages = ["requests", "streamlit"]
    
    for package in packages:
        print(f"正在安裝 {package}...")
        success, _, _ = run_command([sys.executable, "-m", "pip", "install", package, "-q"])
        if success:
            print_status(f"{package} 已安裝", "success")
        else:
            print_status(f"{package} 安裝失敗", "error")
    
    print()
    
    # 第 6 步：驗證安裝
    print(f"{Colors.BOLD}📍 第 6 步：驗證安裝{Colors.RESET}")
    print_separator()
    
    print("驗證 Python 包...")
    
    try:
        import requests
        print_status("requests 已安裝", "success")
    except:
        print_status("requests 驗證失敗", "error")
    
    try:
        import streamlit
        print_status("streamlit 已安裝", "success")
    except:
        print_status("streamlit 驗證失敗", "error")
    
    print("驗證 Ollama...")
    models_ok, stdout, stderr = run_command("ollama list", shell=True)
    if models_ok and "mistral" in stdout.lower():
        print_status("mistral 已安裝", "success")
    
    print()
    
    # 完成
    print_separator()
    print_status("安裝完成！準備開始使用", "success")
    print_separator()
    print()
    
    print(f"{Colors.CYAN}{Colors.BOLD}🚀 立即啟動 CourseHub：{Colors.RESET}")
    print()
    print(f"{Colors.BOLD}  cd 'C:\\Users\\s1015\\OneDrive\\桌面\\CourseHub'")
    print(f"  streamlit run app_streamlit.py{Colors.RESET}")
    print()
    print(f"{Colors.CYAN}✨ 瀏覽器將自動打開 http://localhost:8501{Colors.RESET}")
    print()
    
    print(f"{Colors.YELLOW}💡 首次使用建議：{Colors.RESET}")
    print("   1. 打開 START_HERE.md 了解基本功能")
    print("   2. 點擊左邊欄的「連接 Ollama」按鈕")
    print("   3. 嘗試「智能問答」功能")
    print("   4. 查看「課程推薦」的結果")
    print()
    
    response = input("是否立即啟動系統? (y/n): ").lower()
    
    if response == "y":
        coursehub_dir = r"C:\Users\s1015\OneDrive\桌面\CourseHub"
        os.chdir(coursehub_dir)
        print()
        print(f"{Colors.CYAN}⏳ 啟動中...{Colors.RESET}")
        print()
        
        os.system(f"{sys.executable} -m streamlit run app_streamlit.py")
    else:
        print(f"{Colors.YELLOW}你可以稍後手動運行以上命令{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_status("安裝已取消", "warning")
        sys.exit(0)
    except Exception as e:
        print()
        print_status(f"出錯: {str(e)}", "error")
        sys.exit(1)
