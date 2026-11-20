#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CourseHub RAG + LLM 系統 - 修復版安裝腳本
解決編碼和 Ollama 連接問題
"""

import os
import sys
import subprocess
import time
import requests
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

def run_command(cmd, shell=False, encoding='utf-8', errors='replace'):
    """運行系統命令，使用錯誤容忍編碼"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=False,  # 獲取二進制輸出
            timeout=300
        )
        # 使用錯誤容忍的解碼
        stdout = result.stdout.decode(encoding, errors=errors).strip()
        stderr = result.stderr.decode(encoding, errors=errors).strip()
        return result.returncode == 0, stdout, stderr
    except Exception as e:
        return False, "", str(e)

def check_ollama_api(max_retries=10, timeout=2):
    """檢查 Ollama API 連接"""
    for attempt in range(max_retries):
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=timeout
            )
            if response.status_code == 200:
                return True, response.json()
        except Exception as e:
            if attempt < max_retries - 1:
                print_status(f"等待 Ollama 服務... ({attempt + 1}/{max_retries})", "warning")
                time.sleep(2)
    return False, None

def download_mistral():
    """下載 Mistral 7B 模型"""
    print()
    print_separator()
    print(f"{Colors.BOLD}📥 第 3 步：下載 Mistral 7B 模型{Colors.RESET}")
    print_separator()
    print()
    
    print_status("正在下載 Mistral 7B 模型 (~4GB)...", "info")
    print("⏳ 這可能需要 5-15 分鐘，取決於網速")
    print("🔄 請耐心等待...")
    print()
    
    try:
        # 使用 ollama pull 下載模型，並正確處理輸出
        result = subprocess.Popen(
            ["ollama", "pull", "mistral"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,
            bufsize=1
        )
        
        # 逐行讀取輸出，使用錯誤容忍的解碼
        for line in result.stdout:
            try:
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    print(f"   {decoded_line}")
            except:
                pass
        
        returncode = result.wait()
        
        if returncode == 0:
            print_status("Mistral 7B 模型下載完成！", "success")
            return True
        else:
            print_status("模型下載失敗", "error")
            return False
            
    except Exception as e:
        print_status(f"下載出錯: {str(e)}", "error")
        return False

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print_separator()
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 CourseHub RAG + LLM 系統 - 修復版安裝{Colors.RESET}")
    print_separator()
    print()
    
    # 第 1 步：檢查 Python
    print(f"{Colors.BOLD}📍 第 1 步：檢查 Python{Colors.RESET}")
    print_separator()
    
    version_ok, stdout, _ = run_command([sys.executable, "--version"])
    if version_ok:
        print_status(f"Python 已安裝: {stdout}", "success")
    else:
        print_status("Python 未安裝", "error")
        sys.exit(1)
    
    print()
    
    # 第 2 步：檢查 Ollama
    print(f"{Colors.BOLD}📍 第 2 步：檢查 Ollama{Colors.RESET}")
    print_separator()
    
    ollama_ok, stdout, _ = run_command("ollama --version", shell=True)
    if ollama_ok:
        print_status(f"Ollama 已安裝: {stdout}", "success")
    else:
        print_status("Ollama 未找到", "error")
        print("\n❌ 請先從 https://ollama.ai 安裝 Ollama")
        sys.exit(1)
    
    print()
    print("🔄 檢查 Ollama 服務狀態...")
    api_ok, data = check_ollama_api()
    
    if api_ok:
        print_status("Ollama 服務正在運行", "success")
        if data and 'models' in data:
            print(f"   已安裝的模型: {len(data['models'])} 個")
    else:
        print_status("Ollama 服務未響應", "warning")
        print("\n💡 請在新的 PowerShell 窗口執行:")
        print("   ollama serve")
        print("\n然後返回此窗口重試。")
        sys.exit(1)
    
    print()
    
    # 第 3 步：下載模型
    if download_mistral():
        print()
        print_separator()
        print(f"{Colors.BOLD}📍 第 4 步：安裝 Python 依賴{Colors.RESET}")
        print_separator()
        print()
        
        packages = ["streamlit", "requests", "numpy", "scikit-learn", "pandas"]
        print_status(f"安裝 {len(packages)} 個 Python 包...", "info")
        
        for package in packages:
            print(f"   正在安裝 {package}...")
            cmd = [sys.executable, "-m", "pip", "install", "-q", package]
            success, _, err = run_command(cmd)
            if success:
                print_status(f"✓ {package}", "success")
            else:
                print_status(f"✗ {package}: {err}", "error")
        
        print()
        print_separator()
        print(f"{Colors.BOLD}{Colors.GREEN}✨ 安裝完成！{Colors.RESET}")
        print_separator()
        print()
        print("🎉 所有組件已準備就緒！")
        print()
        print("🚀 啟動 Web UI:")
        print(f"   {Colors.BOLD}streamlit run app_streamlit.py{Colors.RESET}")
        print()
        print("🌐 瀏覽器會自動打開: http://localhost:8501")
        print()
        
        # 詢問是否立即啟動
        response = input("是否現在啟動? (y/n): ").lower()
        if response == "y":
            print()
            print_status("正在啟動 Streamlit...", "info")
            time.sleep(2)
            os.system("streamlit run app_streamlit.py")
    else:
        print_status("模型下載失敗，無法繼續", "error")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_status("安裝被中斷", "warning")
        sys.exit(0)
    except Exception as e:
        print()
        print_status(f"發生錯誤: {str(e)}", "error")
        sys.exit(1)
