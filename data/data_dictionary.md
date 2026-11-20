# CourseHub 課程管理系統 - 資料字典

## 1. 檔案

| 檔案 | 內容 | 時間範圍 |
|---|---|---|
| `students_history.csv` | 所有學生歷史記錄（含畢業生） | 2024-2026 |
| `courses_active.csv` | 目前提供的課程清單 | 2026年度 |
| `enrollments_history.csv` | 選課紀錄（包括退選） | 2024-2026 |
| `prerequisites.csv` | 先修課程對應表 | 固定 |

- 編碼為 UTF-8，第一列為欄位名稱。
- 缺值以空白表示。
- 資料基準日：**2026-11-11**

---

## 2. 計算基準

- **資料基準日：2026-11-11**（目前學年第一學期）
- 學年定義：每年 9 月 - 翌年 6 月，分為上學期（9月-1月）和下學期（2月-6月）
- 年級計算：根據入學年度計算，基準日為大一、二、三、四
- 學分累計：計算至基準日已修課程

---

## 3. 表單欄位定義

### 3.1 students_history.csv

| 欄位 | 說明 | 標準格式／允許值 | 範例 | 敏感等級 |
|---|---|---|---|---|
| StudentID | 學號 | `S` + 7 位數字 | `S2020001` | 一般 |
| Name | 姓名 | 中文名稱 | 王小明 | 敏感 |
| Major | 主修系別 | 見第 4 節 | `EE-電機系` | 一般 |
| GradYear | 預計畢業年份 | YYYY（西元年） | 2027 | 一般 |
| EnrollmentYear | 入學年份 | YYYY | 2024 | 一般 |
| StudentStatus | 學籍狀態 | `Active`、`Graduated`、`Withdrawn`、`On_Leave` | Active | 一般 |
| CurrentGPA | 累積 GPA（至基準日） | 數字，範圍 0.0-4.0，小數兩位 | 3.45 | 高度敏感 |
| CompletedCredits | 已修課程總學分 | 整數，>= 0 | 45 | 一般 |
| TotalCreditsRequired | 畢業所需學分 | 整數，固定值（通常 120-130） | 128 | 一般 |

### 3.2 courses_active.csv

| 欄位 | 說明 | 標準格式／允許值 | 範例 | 敏感等級 |
|---|---|---|---|---|
| CourseID | 課程編號 | `C` + 6 位數字 | `C001001` | 一般 |
| CourseName | 課程名稱 | 中文名稱 | 線性代數(一) | 一般 |
| Department | 開課系別 | 見第 4 節 | `EE-電機系` | 一般 |
| Credits | 學分數 | 整數 (1-4) | 3 | 一般 |
| Capacity | 選課人數上限 | 整數，通常 30-100 | 50 | 一般 |
| Semester | 開課學期 | `2026F` (上)、`2027S` (下) | 2026F | 一般 |
| InstructorID | 教授編號 | `P` + 6 位數字 | `P000001` | 敏感 |
| InstructorName | 教授名稱 | 中文名稱 | 李教授 | 一般 |
| TimeSlots | 上課時間 | JSON 格式：`[{"day":"MON","start":"09:00","end":"11:00"}]` | 見下方例子 | 一般 |
| ClassRoom | 上課教室 | `教室代碼-教室號` | `EE-101` | 一般 |
| Prerequisites | 先修課程編號 | 逗號分隔的課程 ID，空白表示無先修 | `C001001,C001002` | 一般 |
| CourseLevel | 課程等級 | `100`(大一)、`200`(大二)、`300`(大三)、`400`(大四) | 200 | 一般 |
| IsElective | 是否為選修課 | `Y`、`N` | Y | 一般 |
| IsCompulsory | 是否為必修課 | `Y`、`N` | N | 一般 |

**TimeSlots 範例**：
```json
[
  {"day":"MON","start":"09:00","end":"11:00"},
  {"day":"WED","start":"09:00","end":"11:00"}
]
```

### 3.3 enrollments_history.csv

| 欄位 | 說明 | 標準格式／允許值 | 範例 | 敏感等級 |
|---|---|---|---|---|
| EnrollmentID | 選課紀錄編號 | 自增整數 | 123456 | 一般 |
| StudentID | 學號 | `S` + 7 位數字 | `S2020001` | 一般 |
| CourseID | 課程編號 | `C` + 6 位數字 | `C001001` | 一般 |
| Semester | 選課學期 | `2026F` 或 `2027S` | 2026F | 一般 |
| Grade | 成績 | `A`, `B+`, `B`, `C+`, `C`, `D`, `F` 或空白（未評分） | A | 高度敏感 |
| GradePoint | 績點 | 數字，0.0-4.0 | 4.0 | 高度敏感 |
| Status | 選課狀態 | `Enrolled`(已選)、`Withdrawn`(退選)、`Completed`(完成)、`Conflict`(衝突待審) | Enrolled | 一般 |
| EnrollDate | 選課日期 | YYYY-MM-DD | 2026-09-01 | 一般 |
| WithdrawDate | 退選日期 | YYYY-MM-DD，空白表示未退選 | (空白或日期) | 一般 |
| ConflictReason | 衝突原因 | `TimeConflict`(時間衝突)、`CapacityExceeded`(人數超額)、`PrerequisiteFailed`(先修不符) 或空白 | TimeConflict | 一般 |
| ReviewedBy | 審核人員編號 | `A` + 6 位數字，空白表示未審核 | `A000001` | 一般 |
| ReviewedDate | 審核日期 | YYYY-MM-DD，空白表示未審核 | 2026-09-15 | 一般 |

### 3.4 prerequisites.csv

| 欄位 | 說明 | 標準格式／允許值 | 範例 | 敏感等級 |
|---|---|---|---|---|
| CourseID | 課程編號 | `C` + 6 位數字 | `C001002` | 一般 |
| PrerequisiteCourseID | 先修課程編號 | `C` + 6 位數字 | `C001001` | 一般 |
| IsStrict | 是否為硬性先修 | `Y`(必須通過)、`N`(建議先修) | Y | 一般 |

---

## 4. 系別清單

| 系別代碼 | 系別名稱 | 英文名稱 | 課程數 | 學生數 |
|---|---|---|---|---|
| EE | 電機系 | Electrical Engineering | 18 | 250 |
| CE | 電子系 | Electronics Engineering | 16 | 220 |
| CS | 資訊系 | Computer Science | 20 | 280 |
| ME | 機械系 | Mechanical Engineering | 15 | 200 |
| CH | 化工系 | Chemical Engineering | 12 | 160 |
| CV | 土木系 | Civil Engineering | 14 | 180 |
| BIO | 生物系 | Biology | 13 | 170 |
| CHEM | 化學系 | Chemistry | 11 | 150 |
| PHY | 物理系 | Physics | 10 | 130 |
| MATH | 數學系 | Mathematics | 14 | 180 |
| BUS | 商學系 | Business Administration | 17 | 220 |
| MUS | 音樂系 | Music | 9 | 100 |

**小計**：12 個系別，約 200 門課程，2,000 名學生

---

## 5. 資料規則

1. 每位學生只有一筆現況資料；歷史選課紀錄在 enrollments_history.csv
2. 已選課程的 Grade 欄位在評分前為空白
3. TimeSlots 必須是合法的 JSON；若格式錯誤，視為無效資料
4. Status 為 `Conflict` 的選課記錄必須有 ConflictReason 和待審核狀態（ReviewedBy 為空）
5. 如果選課衝突已被人工審核通過（Status = `Enrolled`），则 ConflictReason 應保留但 ReviewedBy 需填入審核者
6. 合法年級：大一(1)、大二(2)、大三(3)、大四(4)
7. CurrentGPA 範圍：0.0 - 4.0；不在範圍內視為無效值

---

## 6. 無效值處理原則

- 不在合法範圍內、或無法依本文件判定的值，視為缺值。
- 計算需要使用該欄位的指標時，排除該筆資料，並在回答中說明排除的筆數。
- 不得自行推估或補值。
- 該筆資料的其他欄位不受影響，仍納入其他計算。

---

## 7. 敏感資訊分類

| 敏感等級 | 包含資訊 | 存取權限 |
|---|---|---|
| 一般 | 課程編號、系別、學分、時間表 | 所有登入角色 |
| 敏感 | 學生姓名、教授名稱、教室位置 | R1(本人)、R2(教授自己的課)、R3+以上 |
| 高度敏感 | 成績、GPA、績點 | R1(本人只看自己)、R2(教授看自己班級)、R4+(管理人員) |

---

## 8. 系統常數

| 常數 | 值 | 說明 |
|---|---|---|
| BASE_DATE | 2026-11-11 | 資料基準日期 |
| CURRENT_SEMESTER | 2026F | 目前學期（上學期） |
| MIN_GPA_SCALE | 0.0 | GPA 最低分 |
| MAX_GPA_SCALE | 4.0 | GPA 最高分 |
| CREDITS_PER_SEMESTER_MIN | 9 | 每學期最少選課學分 |
| CREDITS_PER_SEMESTER_MAX | 25 | 每學期最多選課學分 |
| COURSE_NAME_PATTERN | `C\d{6}` | 課程編號正則 |
| STUDENT_ID_PATTERN | `S\d{7}` | 學號正則 |

