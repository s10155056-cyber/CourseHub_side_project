# CourseHub

CourseHub 是一個大學選課管理 side project，結合課程資料檢索、Ollama 本地語言模型，以及選課規則與權限管理示範。

> **專案現況：** Repository 包含兩個獨立的應用程式：根目錄的 Streamlit 課程助理，以及 `code/` 中的 Flask 選課 API。兩者目前尚未整合成同一個系統。

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![Flask](https://img.shields.io/badge/API-Flask-black)
![Database](https://img.shields.io/badge/Database-SQLite-blue)

## 功能一覽

### Streamlit 課程助理

- 使用課程資料進行檢索，並由 Ollama 本地模型生成回答。
- 提供課程搜尋與推薦、學習計劃及選課衝突解決等介面。
- 預設使用 `mistral` 模型，Ollama 服務預設網址為 `http://localhost:11434`。

### Flask 選課 API

- 提供登入、課程與選課相關 API。
- 示範 R1–R5 角色權限、課程先修／時間／容量檢查及衝突審核流程。
- 使用 SQLite 儲存應用資料，並包含稽核紀錄功能。

## 架構

```text
CourseHub/
├── app_streamlit.py       # Streamlit 課程助理介面
├── rag_system.py          # 課程檢索與 Ollama 整合
├── code/
│   ├── app.py             # Flask 選課 API
│   ├── coursehub.py       # 選課、權限與資料處理邏輯
│   ├── requirements.txt   # Flask API 依賴
│   ├── test_coursehub.py  # API 專案測試
│   └── data/              # Flask API 使用的範例資料
├── data/                  # 資料字典
└── *.csv                  # 根目錄的範例 CSV
```

`code/data/` 內含課程、學生、選課紀錄與先修資料。根目錄的 CSV 是另一組範例資料檔；請留意各應用程式目前讀取的路徑不同。

## 執行 Flask API

需要 Python 3 與 pip。以下以 Windows PowerShell 為例：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install Flask==2.3.3 Werkzeug==2.3.7
cd code
python app.py
```

API 預設在 `http://localhost:5000` 啟動，健康檢查端點為 `/health`。

建立管理員帳號（依提示輸入密碼）：

```powershell
python app.py --create-admin admin
```

建立完成後，再執行 `python app.py` 啟動 API。資料庫與執行期日誌預設會放在 `code/.runtime/`。

## 執行 Streamlit 課程助理

需要 Python、Streamlit、Requests，以及已啟動的 Ollama。先下載預設模型：

```powershell
ollama pull mistral
pip install streamlit requests
streamlit run app_streamlit.py
```

啟動網頁後，使用側邊欄的「連接 Ollama」按鈕連線。

> **目前限制：** `app_streamlit.py` 使用開發者電腦上的絕對路徑，且助理預期課程資料位於專案根目錄的 `data/`；目前實際 CSV 位於 `code/data/`。因此在其他電腦上執行前，需要先修正應用程式的專案路徑與資料目錄設定。

## 執行測試

```powershell
cd code
python test_coursehub.py
```

## 安全提醒

- Flask API 的開發密鑰預設值不可用於正式環境。部署前請設定 `COURSEHUB_SECRET_KEY` 為隨機且保密的值。
- 目前專案定位為課程示範；對外部署前，請另行檢查認證、部署設定、資料保護與 API 安全性。
- 請勿將 `.env`、密鑰、真實個人資料或本機資料庫提交至公開 Repository。
