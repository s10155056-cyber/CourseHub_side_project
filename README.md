# CourseHub - 智慧課程管理系統

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![SQLite](https://img.shields.io/badge/SQLite-3-lightblue)
![License](https://img.shields.io/badge/License-MIT-orange)

**CourseHub** 是為大學教務系統設計的智慧選課平台，具有多層次權限控制、選課衝突檢測、先修課程驗證和混合型人工審核機制。

## 📋 目錄

- [特性](#-特性)
- [系統架構](#-系統架構)
- [快速開始](#-快速開始)
- [API 文檔](#-api-文檔)
- [權限系統](#-權限系統)
- [技術棧](#-技術棧)
- [測試](#-測試)

---

## ✨ 特性

### 核心功能

- ✅ **多角色權限管理** - 5 層權限體系（R1-R5），精細化資料範圍控制
- ✅ **時間衝突檢測** - 自動比對課程時間，防止時間表衝突
- ✅ **先修課程驗證** - 檢查學生是否已修完必修先修課程
- ✅ **課程容量管理** - 追蹤選課人數，防止超額
- ✅ **混合型衝突審核** - 系統自動檢測，衝突由教務人員人工審核
- ✅ **GPA 自動計算** - 根據成績自動累計績點
- ✅ **完整稽核追蹤** - 所有操作記錄於日誌，便於追責

### 資料安全

- 🔐 **密碼雜湊儲存** - HMAC-SHA256 with salt
- 🔐 **工作階段管理** - Cookie-based sessions
- 🔐 **個資保護** - 敏感資訊分層隔離，符合隱私要求
- 🔐 **稽核日誌** - 記錄所有查詢和操作，不保存原始問題

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────┐
│                  Web Frontend (HTML/JS)             │
│              登入 / 選課 / 成績查詢 / 審核           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          Flask API (app.py)                         │
│     登入管理 / 路由 / 工作階段控制 / 權限檢查        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│    Core Logic (coursehub.py)                        │
│  ┌──────────────────────────────────────────────┐   │
│  │ ✓ 選課邏輯（先修、衝突、容量）               │   │
│  │ ✓ 權限控制與資料過濾                         │   │
│  │ ✓ 資料驗證與清理                             │   │
│  │ ✓ 稽核日誌記錄                               │   │
│  └──────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│     SQLite Database (.runtime/coursehub.sqlite)     │
│  ┌──────────────────────────────────────────────┐   │
│  │ students, courses, enrollments               │   │
│  │ prerequisites, users, sessions               │   │
│  │ audit_logs, data_cleaning_records            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│      CSV 資料來源 (data/)                           │
│  students_history.csv (2000 名學生)                 │
│  courses_active.csv (192 門課程)                    │
│  enrollments_history.csv (22873 筆選課)             │
│  prerequisites.csv (144 先修關係)                   │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 快速開始

### 前置要求

- Python 3.8+
- pip (Python 套件管理)

### 安裝

```bash
# 1. 克隆或下載專案
cd CourseHub

# 2. 進入代碼目錄
cd code

# 3. 安裝依賴（若需要）
pip install flask

# 4. 初始化數據庫並建立管理員
python app.py --create-admin admin

# 5. 啟動服務
python app.py

# 6. 訪問系統
# 本機網址：http://localhost:5000
```

### 環境變數

```bash
# 設置資料目錄
export COURSEHUB_DATA_DIR=/path/to/data

# 設置資料庫路徑
export COURSEHUB_DB_PATH=/path/to/coursehub.sqlite

# 設置日誌目錄
export COURSEHUB_LOG_DIR=/path/to/logs

# 設置 Flask 密鑰（生產環境必須）
export COURSEHUB_SECRET_KEY=your-secret-key-here

# 啟用 AI 功能（可選）
export COURSEHUB_FOUNDRY_ENABLED=1
export COURSEHUB_FOUNDRY_ENDPOINT=https://api.foundry.example.com
export COURSEHUB_FOUNDRY_API_KEY=your-api-key
```

---

## 📖 API 文檔

### 認證

#### 登入
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "student_001",
  "password": "password"
}

# 響應 (200 OK)
{
  "message": "登入成功",
  "username": "student_001",
  "role": "R1"
}
```

#### 登出
```bash
POST /api/auth/logout

# 響應 (200 OK)
{
  "message": "登出成功"
}
```

#### 查詢目前使用者
```bash
GET /api/auth/me

# 響應 (200 OK)
{
  "username": "student_001",
  "role": "R1",
  "scope": "student:S2020001"
}
```

---

### 學生選課 (R1)

#### 查詢自己的選課紀錄
```bash
GET /api/student/enrollments

# 響應 (200 OK)
[
  {
    "enrollment_id": 1,
    "course_id": "C001001",
    "course_name": "線性代數(一)",
    "semester": "2026F",
    "grade": "A",
    "status": "Completed",
    "conflict_reason": null,
    "enroll_date": "2026-09-01"
  },
  ...
]
```

#### 選課
```bash
POST /api/student/enroll
Content-Type: application/json

{
  "course_id": "C001002"
}

# 響應 (201 Created)
{
  "message": "選課申請已提交",
  "status": "Enrolled",        # 或 "Conflict" 如有衝突
  "conflict_reason": null      # "TimeConflict" / "PrerequisiteFailed" / "CapacityExceeded"
}
```

#### 退選
```bash
POST /api/student/withdraw
Content-Type: application/json

{
  "enrollment_id": 1
}

# 響應 (200 OK)
{
  "message": "已退選"
}
```

---

### 教授查詢 (R2)

#### 查詢自己教授的課程
```bash
GET /api/professor/courses

# 響應 (200 OK)
[
  {
    "course_id": "C001001",
    "course_name": "線性代數(一)",
    "department": "MATH",
    "credits": 3,
    "capacity": 50,
    "semester": "2026F",
    "instructor_id": "P000001",
    "time_slots": "[{\"day\":\"MON\",\"start\":\"09:00\",\"end\":\"11:00\"}]"
  },
  ...
]
```

#### 查詢班級名單
```bash
GET /api/professor/roster/C001001

# 響應 (200 OK)
[
  {
    "student_id": "S2020001",
    "name": "王小明",
    "enrollment_id": 1,
    "grade": "A",
    "status": "Enrolled"
  },
  ...
]
```

---

### 教務查詢 (R3/R4/R5)

#### 查詢待審核的衝突選課
```bash
GET /api/admin/conflicts

# 響應 (200 OK)
[
  {
    "enrollment_id": 15,
    "student_id": "S2020001",
    "name": "王小明",
    "course_id": "C001002",
    "course_name": "微積分",
    "conflict_reason": "TimeConflict",
    "enroll_date": "2026-09-05"
  },
  ...
]
```

---

### 管理員操作 (R5)

#### 導入學生資料
```bash
POST /api/admin/import/students

# 響應 (200 OK)
{
  "message": "學生資料導入完成",
  "stats": {
    "total": 2000,
    "valid": 1998,
    "invalid": 2,
    "duplicates": 0,
    "conflicts": 0
  }
}
```

---

## 🔐 權限系統

### 5 層角色體系

| 角色 | 代碼 | 職責 | 主要操作 |
|---|---|---|---|
| 學生 | R1 | 查看自己的選課狀況和成績 | 選課、退選、查詢成績 |
| 教授 | R2 | 管理自己教授的課程 | 查看班級、批改成績 |
| 系主任 | R3 | 監督系內課程和教務 | 查詢系內資料、審核衝突 |
| 教務人員 | R4 | 解決選課衝突 | 人工審核、衝突解決 |
| 管理員 | R5 | 系統管理和資料維護 | 導入資料、清理、配置 |

### 權限矩陣範例

| 功能 | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| 查詢自己的選課 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 查詢他人選課 | ❌ | ✅(自班級) | ✅(系內) | ✅(全校) | ✅ |
| 選課 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 審核衝突 | ❌ | ❌ | ✅(系內) | ✅(全校) | ✅ |
| 導入資料 | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🛠️ 技術棧

| 組件 | 技術 | 版本 |
|---|---|---|
| 後端框架 | Flask | 2.0+ |
| 資料庫 | SQLite | 3 |
| 認證 | HMAC-SHA256 + Sessions | - |
| 資料驗證 | Python 內建 | - |
| 測試框架 | pytest（可選） | 6.0+ |
| API 文檔 | 本 README | - |

---

## ✅ 測試

### 運行評測集

```bash
cd code
python test_coursehub.py
```

### 評測結果摘要

```
============================================================
CourseHub 自動化評測集
============================================================

✅ 通過：10/10
❌ 失敗：0
📊 通過率：100.0%

評測內容：
 1. ✅ R1 學生能查詢自己的選課
 2. ✅ R1 學生無法查詢其他學生的選課
 3. ✅ 時間衝突檢測
 4. ✅ 先修課程檢測
 5. ✅ 容量超額檢測
 6. ✅ 混合型審核：衝突被自動檢測
 7. ✅ R3 系主任只能看自己系的資料
 8. ✅ R2 教授只能看自己教的課
 9. ✅ R4 教務人員可以審核全校衝突
10. ✅ R5 管理員擁有所有權限
```

---

## 📊 數據統計

### 模擬資料集規模

- **學生數**：2,000 名（涵蓋大一至大四）
- **課程數**：192 門（來自 12 個系別）
- **選課紀錄**：22,873 筆（3 學年歷史）
- **先修關係**：144 條

### 資料基準日期

- **基準日**：2026 年 11 月 11 日
- **目前學期**：2026 年上學期（2026F）
- **涵蓋範圍**：2024 年 9 月 - 2026 年 11 月

---

## 🎯 核心業務邏輯

### 選課流程

```
1. 學生提交選課請求
   ↓
2. [R1 權限檢查] ✓ 該學生已登入
   ↓
3. [先修檢查] 是否已修完先修課程？
   ↓
4. [時間衝突檢查] 是否與已選課程時間重疊？
   ↓
5. [容量檢查] 課程是否已滿？
   ↓
6. 若無衝突 → enrollment.status = 'Enrolled'
   若有衝突 → enrollment.status = 'Conflict' → 等待審核
   ↓
7. [R4 教務人員] 人工審核衝突（混合型）
   ↓
8. 決定：通過 / 駁回 / 建議替代課程
```

### 先修課程檢測演算法

```python
def check_prerequisite(student_id, course_id):
    prerequisites = get_course_prerequisites(course_id)
    
    for prereq_course_id in prerequisites:
        if not has_completed(student_id, prereq_course_id):
            return False, f"未修完先修課程 {prereq_course_id}"
    
    return True, None
```

### 時間衝突檢測演算法

```python
def check_time_conflict(slots1, slots2):
    # slots1, slots2 是 JSON 格式的時間表
    for s1 in parse_slots(slots1):
        for s2 in parse_slots(slots2):
            if s1['day'] == s2['day']:
                if time_overlap(s1['start'], s1['end'], s2['start'], s2['end']):
                    return True
    return False
```

---

## 📝 資料字典

詳見 `data/data_dictionary.md`

### 主要表結構

| 表名 | 功能 | 行數 |
|---|---|---|
| students | 學生主資料 | 2,000 |
| courses | 課程主資料 | 192 |
| enrollments | 選課紀錄 | 22,873 |
| prerequisites | 先修課程對應 | 144 |
| users | 系統使用者 | N/A |
| sessions | 工作階段 | 臨時 |
| audit_logs | 稽核日誌 | 累積 |

---

## 🤝 貢獻指南

歡迎提交問題和改進建議！

```bash
# 1. 克隆專案
git clone <repository>

# 2. 建立功能分支
git checkout -b feature/your-feature

# 3. 提交更改
git commit -am "Add your feature"

# 4. 推送到遠端
git push origin feature/your-feature

# 5. 建立 Pull Request
```

---

## 📄 許可證

本專案採用 MIT 許可證。詳見 [LICENSE](LICENSE) 檔案。

---

## 📧 聯絡方式

如有問題或建議，請通過以下方式聯絡：

- 📧 Email: support@coursehub.example.com
- 🐛 Issue Tracker: [GitHub Issues]
- 💬 Discussion: [GitHub Discussions]

---

## 🙏 致謝

感謝所有貢獻者和使用者的支持！

---

**最後更新**：2026 年 11 月 11 日

#   C o u r s e H u b _ s i d e _ p r o j e c t  
 #   C o u r s e H u b _ s i d e _ p r o j e c t  
 