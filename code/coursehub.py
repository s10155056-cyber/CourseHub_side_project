"""
CourseHub 核心業務邏輯模塊

包含：
- 數據驗證和清理
- 選課邏輯（先修檢查、時間衝突、容量管理）
- 混合型衝突審核
- 權限控制
- 稽核日誌
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import sqlite3
import secrets
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ==================== 常數 ====================

BASE_DATE = date(2026, 11, 11)
CURRENT_SEMESTER = "2026F"

# 系別清單
DEPARTMENTS = {"EE", "CE", "CS", "ME", "CH", "CV", "BIO", "CHEM", "PHY", "MATH", "BUS", "MUS"}

# 角色定義
ROLES = {"R1", "R2", "R3", "R4", "R5"}

# 學籍狀態
STUDENT_STATUSES = {"Active", "Graduated", "Withdrawn", "On_Leave"}

# 選課狀態
ENROLLMENT_STATUSES = {"Enrolled", "Withdrawn", "Completed", "Conflict"}

# 成績對應績點
GRADE_POINTS = {
    "A": 4.0,
    "B+": 3.7,
    "B": 3.3,
    "C+": 3.0,
    "C": 2.7,
    "D": 2.3,
    "F": 0.0,
}

# 衝突原因
CONFLICT_REASONS = {"TimeConflict", "CapacityExceeded", "PrerequisiteFailed"}

# 可選的 Foundry Claude 模型
FOUNDRY_MODELS = {
    "claude-haiku-5-5",
    "claude-sonnet-5-5",
    "claude-opus-5-5",
}


class CourseHubError(Exception):
    """系統預期的、使用者安全的應用錯誤"""
    pass


# ==================== 數據庫連接 ====================

def connect(db_path: Path) -> sqlite3.Connection:
    """建立數據庫連接"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize(db_path: Path) -> None:
    """初始化數據庫"""
    with connect(db_path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_salt BLOB NOT NULL,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('R1','R2','R3','R4','R5')),
                scope TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                username TEXT NOT NULL REFERENCES users(username),
                expires_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS students (
                row_id INTEGER PRIMARY KEY,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                major TEXT NOT NULL,
                grad_year INTEGER NOT NULL,
                enrollment_year INTEGER NOT NULL,
                student_status TEXT NOT NULL,
                current_gpa REAL DEFAULT 0.0,
                completed_credits INTEGER DEFAULT 0,
                total_credits_required INTEGER NOT NULL,
                data_json TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS courses (
                row_id INTEGER PRIMARY KEY,
                course_id TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                department TEXT NOT NULL,
                credits INTEGER NOT NULL,
                capacity INTEGER NOT NULL,
                semester TEXT NOT NULL,
                instructor_id TEXT NOT NULL,
                instructor_name TEXT NOT NULL,
                time_slots TEXT NOT NULL,
                classroom TEXT,
                prerequisites TEXT,
                course_level INTEGER NOT NULL,
                is_elective TEXT NOT NULL,
                is_compulsory TEXT NOT NULL,
                data_json TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL REFERENCES students(student_id),
                course_id TEXT NOT NULL REFERENCES courses(course_id),
                semester TEXT NOT NULL,
                grade TEXT,
                grade_point REAL,
                status TEXT NOT NULL,
                enroll_date TEXT NOT NULL,
                withdraw_date TEXT,
                conflict_reason TEXT,
                reviewed_by TEXT,
                reviewed_date TEXT,
                UNIQUE(student_id, course_id, semester)
            );
            
            CREATE TABLE IF NOT EXISTS prerequisites (
                course_id TEXT NOT NULL REFERENCES courses(course_id),
                prerequisite_course_id TEXT NOT NULL,
                is_strict TEXT NOT NULL,
                PRIMARY KEY (course_id, prerequisite_course_id)
            );
            
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                user_role TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                timestamp TEXT NOT NULL,
                query_scope TEXT,
                result_count INTEGER,
                status TEXT NOT NULL,
                error_message TEXT
            );
            
            CREATE TABLE IF NOT EXISTS data_cleaning_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_batch_id TEXT NOT NULL,
                table_name TEXT NOT NULL,
                total_rows INTEGER NOT NULL,
                valid_rows INTEGER NOT NULL,
                invalid_rows INTEGER NOT NULL,
                duplicates_removed INTEGER NOT NULL,
                conflicts_flagged INTEGER NOT NULL,
                cleaning_details TEXT,
                cleaned_by TEXT NOT NULL,
                cleaned_at TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_students_major ON students(major);
            CREATE INDEX IF NOT EXISTS idx_students_status ON students(student_status);
            CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department);
            CREATE INDEX IF NOT EXISTS idx_courses_semester ON courses(semester);
            CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
            CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
            CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
        """)
        db.commit()


# ==================== 認證和權限 ====================

def hash_password(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """對密碼進行雜湊（HMAC-SHA256）"""
    if salt is None:
        salt = secrets.token_bytes(32)
    password_hash = hmac.new(salt, password.encode(), hashlib.sha256).digest()
    return salt, password_hash


def verify_password(password: str, salt: bytes, password_hash: bytes) -> bool:
    """驗證密碼"""
    _, computed_hash = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def create_session_token() -> str:
    """建立工作階段令牌"""
    return secrets.token_urlsafe(32)


# ==================== 資料驗證 ====================

def validate_student_record(record: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """驗證單筆學生紀錄"""
    try:
        if not record.get('StudentID', '').startswith('S'):
            return False, "StudentID 格式不正確"
        if record.get('StudentStatus') not in STUDENT_STATUSES:
            return False, f"StudentStatus 不在允許值內：{STUDENT_STATUSES}"
        if record.get('Major') not in DEPARTMENTS:
            return False, f"Major 系別不存在"
        
        gpa = float(record.get('CurrentGPA', 0))
        if not (0.0 <= gpa <= 4.0):
            return False, "CurrentGPA 超出範圍 [0.0, 4.0]"
        
        return True, None
    except Exception as e:
        return False, str(e)


def validate_course_record(record: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """驗證單筆課程紀錄"""
    try:
        if not record.get('CourseID', '').startswith('C'):
            return False, "CourseID 格式不正確"
        if record.get('Department') not in DEPARTMENTS:
            return False, f"Department 系別不存在"
        
        # 驗證 TimeSlots JSON
        try:
            json.loads(record.get('TimeSlots', '[]'))
        except json.JSONDecodeError:
            return False, "TimeSlots 不是有效的 JSON"
        
        capacity = int(record.get('Capacity', 0))
        if capacity <= 0:
            return False, "Capacity 必須大於 0"
        
        return True, None
    except Exception as e:
        return False, str(e)


# ==================== 選課業務邏輯 ====================

def check_time_conflict(slots1: str, slots2: str) -> bool:
    """檢查兩個時間表是否衝突"""
    try:
        s1 = json.loads(slots1)
        s2 = json.loads(slots2)
        
        for slot1 in s1:
            for slot2 in s2:
                if slot1.get('day') == slot2.get('day'):
                    start1 = int(slot1.get('start', '0:0').split(':')[0])
                    end1 = int(slot1.get('end', '0:0').split(':')[0])
                    start2 = int(slot2.get('start', '0:0').split(':')[0])
                    end2 = int(slot2.get('end', '0:0').split(':')[0])
                    
                    # 時間段重疊判定
                    if (start1 < end2) and (start2 < end1):
                        return True
        return False
    except:
        return False


def check_prerequisite(db: sqlite3.Connection, student_id: str, course_id: str) -> Tuple[bool, Optional[str]]:
    """檢查學生是否滿足先修課程要求
    
    返回：(是否滿足, 錯誤訊息)
    """
    # 查詢該課程的先修課程
    cursor = db.execute("""
        SELECT prerequisite_course_id, is_strict FROM prerequisites
        WHERE course_id = ?
    """, (course_id,))
    
    prerequisites = cursor.fetchall()
    if not prerequisites:
        return True, None
    
    # 檢查學生是否已完成先修課程
    for prereq in prerequisites:
        prereq_course_id = prereq['prerequisite_course_id']
        is_strict = prereq['is_strict'] == 'Y'
        
        cursor = db.execute("""
            SELECT grade FROM enrollments
            WHERE student_id = ? AND course_id = ? AND status = 'Completed'
        """, (student_id, prereq_course_id))
        
        completion = cursor.fetchone()
        
        if not completion or completion['grade'] == 'F':
            if is_strict:
                return False, f"未滿足硬性先修課程要求：{prereq_course_id}"
    
    return True, None


def check_capacity(db: sqlite3.Connection, course_id: str) -> Tuple[bool, int, int]:
    """檢查課程是否已滿
    
    返回：(未超額, 已選人數, 容量)
    """
    cursor = db.execute("""
        SELECT c.capacity, COUNT(e.enrollment_id) AS enrolled_count
        FROM courses c
        LEFT JOIN enrollments e ON c.course_id = e.course_id 
            AND e.status IN ('Enrolled', 'Completed')
        WHERE c.course_id = ?
        GROUP BY c.course_id
    """, (course_id,))
    
    result = cursor.fetchone()
    if not result:
        return True, 0, 0
    
    capacity = result['capacity']
    enrolled_count = result['enrolled_count'] or 0
    
    return enrolled_count < capacity, enrolled_count, capacity


def auto_detect_conflicts(db: sqlite3.Connection, student_id: str, course_id: str) -> Optional[str]:
    """自動檢測選課衝突（混合型審核的第一步）
    
    返回：衝突原因，若無衝突則返回 None
    """
    
    # 1. 檢查先修課程
    satisfied, error = check_prerequisite(db, student_id, course_id)
    if not satisfied:
        return "PrerequisiteFailed"
    
    # 2. 檢查容量
    not_full, _, _ = check_capacity(db, course_id)
    if not not_full:
        return "CapacityExceeded"
    
    # 3. 檢查時間衝突
    cursor = db.execute("""
        SELECT c.time_slots
        FROM courses c
        WHERE c.course_id = ?
    """, (course_id,))
    
    new_course = cursor.fetchone()
    if new_course:
        new_slots = new_course['time_slots']
        
        cursor = db.execute("""
            SELECT c.time_slots
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = ? AND e.status IN ('Enrolled', 'Completed')
        """, (student_id,))
        
        for existing in cursor.fetchall():
            if check_time_conflict(new_slots, existing['time_slots']):
                return "TimeConflict"
    
    return None


# ==================== 數據導入和清理 ====================

def import_students_from_csv(db: sqlite3.Connection, csv_path: Path, cleaned_by: str) -> Dict[str, int]:
    """從 CSV 導入學生資料並清理"""
    import_batch_id = f"students_{datetime.now().isoformat()}"
    stats = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'duplicates': 0,
        'conflicts': 0,
    }
    
    seen_ids = set()
    invalid_records = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats['total'] += 1
            
            # 檢查重複
            if row['StudentID'] in seen_ids:
                stats['duplicates'] += 1
                continue
            seen_ids.add(row['StudentID'])
            
            # 驗證紀錄
            valid, error = validate_student_record(row)
            if not valid:
                stats['invalid'] += 1
                invalid_records.append((row['StudentID'], error))
                continue
            
            # 插入資料庫
            try:
                db.execute("""
                    INSERT INTO students 
                    (student_id, name, major, grad_year, enrollment_year, student_status, 
                     current_gpa, completed_credits, total_credits_required, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['StudentID'],
                    row['Name'],
                    row['Major'],
                    int(row['GradYear']),
                    int(row['EnrollmentYear']),
                    row['StudentStatus'],
                    float(row.get('CurrentGPA', 0)),
                    int(row.get('CompletedCredits', 0)),
                    int(row.get('TotalCreditsRequired', 128)),
                    json.dumps(row, ensure_ascii=False),
                ))
                stats['valid'] += 1
            except sqlite3.IntegrityError as e:
                stats['conflicts'] += 1
    
    db.commit()
    
    # 記錄清理報告
    db.execute("""
        INSERT INTO data_cleaning_records
        (import_batch_id, table_name, total_rows, valid_rows, invalid_rows,
         duplicates_removed, conflicts_flagged, cleaning_details, cleaned_by, cleaned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        import_batch_id,
        'students',
        stats['total'],
        stats['valid'],
        stats['invalid'],
        stats['duplicates'],
        stats['conflicts'],
        json.dumps({'invalid_details': invalid_records}, ensure_ascii=False),
        cleaned_by,
        datetime.now().isoformat(),
    ))
    db.commit()
    
    return stats


# ==================== 稽核日誌 ====================

def log_action(db: sqlite3.Connection, username: str, user_role: str, action: str,
               resource_type: Optional[str] = None, resource_id: Optional[str] = None,
               query_scope: Optional[str] = None, result_count: int = 0,
               status: str = "success", error_message: Optional[str] = None):
    """記錄使用者操作"""
    db.execute("""
        INSERT INTO audit_logs
        (username, user_role, action, resource_type, resource_id, timestamp,
         query_scope, result_count, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        username,
        user_role,
        action,
        resource_type,
        resource_id,
        datetime.now().isoformat(),
        query_scope,
        result_count,
        status,
        error_message,
    ))
    db.commit()


# ==================== 權限檢查 ====================

def check_permission(db: sqlite3.Connection, username: str, action: str,
                     resource_type: str, resource_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """檢查使用者是否有權執行操作"""
    cursor = db.execute("""
        SELECT role, scope FROM users WHERE username = ? AND active = 1
    """, (username,))
    
    user = cursor.fetchone()
    if not user:
        return False, "使用者不存在或已停用"
    
    role = user['role']
    scope = user['scope']
    
    # R5 管理員擁有所有權限
    if role == 'R5':
        return True, None
    
    # R1 學生：只能查看和操作自己的資料
    if role == 'R1':
        if resource_type == 'enrollment' and resource_id:
            student_id = scope.split(':')[1]  # 格式：student:S2020001
            cursor = db.execute("""
                SELECT student_id FROM enrollments WHERE enrollment_id = ?
            """, (resource_id,))
            result = cursor.fetchone()
            if result and result['student_id'] != student_id:
                return False, "你無權存取其他學生的資料"
        return True, None
    
    # R2 教授：只能查看自己教的課程
    if role == 'R2':
        if resource_type == 'course' and resource_id:
            prof_id = scope.split(':')[1]  # 格式：professor:P000001
            cursor = db.execute("""
                SELECT instructor_id FROM courses WHERE course_id = ?
            """, (resource_id,))
            result = cursor.fetchone()
            if result and result['instructor_id'] != prof_id:
                return False, "你無權存取其他教授的課程"
        return True, None
    
    # R3 系主任：只能查看系內資料
    if role == 'R3':
        if resource_type == 'student' and resource_id:
            dept = scope.split(':')[1]  # 格式：department:CS
            cursor = db.execute("""
                SELECT major FROM students WHERE student_id = ?
            """, (resource_id,))
            result = cursor.fetchone()
            if result and result['major'] != dept:
                return False, "你無權存取其他系的學生資料"
        return True, None
    
    # R4 教務人員：可以查看全校但只能操作衝突審核
    if role == 'R4':
        if action in ['approve_conflict', 'reject_conflict']:
            return True, None
        if action == 'query_all':
            return True, None
        return False, "教務人員只能進行衝突審核"
    
    return False, "權限不足"


print("✅ CourseHub 核心模塊已載入")
