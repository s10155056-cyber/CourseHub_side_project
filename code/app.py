#!/usr/bin/env python3
"""
CourseHub Web API 服務

提供 HTTP 接口用於：
- 使用者登入和工作階段管理
- 學生選課和退選
- 教授查看班級
- 系主任查詢系內資料
- 教務人員審核衝突
- 管理員資料管理
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from flask import Flask, request, jsonify, session as flask_session
from werkzeug.security import generate_password_hash

import coursehub as ch

# ==================== Flask 應用初始化 ====================

app = Flask(__name__)
app.secret_key = os.environ.get('COURSEHUB_SECRET_KEY', 'dev-secret-key-change-in-production')

# 配置
COURSEHUB_DATA_DIR = Path(os.environ.get('COURSEHUB_DATA_DIR', Path(__file__).parent / 'data'))
COURSEHUB_DB_PATH = Path(os.environ.get('COURSEHUB_DB_PATH', Path(__file__).parent / '.runtime' / 'coursehub.sqlite'))
COURSEHUB_LOG_DIR = Path(os.environ.get('COURSEHUB_LOG_DIR', Path(__file__).parent / '.runtime' / 'logs'))


def get_db():
    """取得數據庫連接"""
    return ch.connect(COURSEHUB_DB_PATH)


def get_current_user() -> Optional[Tuple[str, str, str]]:
    """從 session 中取得目前登入的使用者
    
    返回：(username, role, scope)，若未登入則返回 None
    """
    if 'username' not in flask_session:
        return None
    
    username = flask_session['username']
    db = get_db()
    cursor = db.execute("""
        SELECT role, scope FROM users WHERE username = ? AND active = 1
    """, (username,))
    
    result = cursor.fetchone()
    db.close()
    
    if result:
        return username, result['role'], result['scope']
    
    return None


# ==================== 認證端點 ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """使用者登入"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '使用者名稱和密碼不能為空'}), 400
    
    db = get_db()
    cursor = db.execute("""
        SELECT password_salt, password_hash, role, scope, active FROM users
        WHERE username = ?
    """, (username,))
    
    user = cursor.fetchone()
    db.close()
    
    if not user or user['active'] == 0:
        ch.log_action(None, username, 'unknown', 'login', status='denied', 
                     error_message='使用者不存在或已停用')
        return jsonify({'error': '使用者名稱或密碼錯誤'}), 401
    
    # 驗證密碼
    if not ch.verify_password(password, user['password_salt'], user['password_hash']):
        return jsonify({'error': '使用者名稱或密碼錯誤'}), 401
    
    # 建立 session
    flask_session['username'] = username
    flask_session['role'] = user['role']
    flask_session['scope'] = user['scope']
    flask_session.permanent = True
    
    return jsonify({
        'message': '登入成功',
        'username': username,
        'role': user['role'],
    }), 200


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """使用者登出"""
    user_info = get_current_user()
    if user_info:
        flask_session.clear()
    
    return jsonify({'message': '登出成功'}), 200


@app.route('/api/auth/me', methods=['GET'])
def get_me():
    """取得目前登入使用者的資訊"""
    user_info = get_current_user()
    
    if not user_info:
        return jsonify({'error': '未登入'}), 401
    
    username, role, scope = user_info
    return jsonify({
        'username': username,
        'role': role,
        'scope': scope,
    }), 200


# ==================== 學生選課端點 ====================

@app.route('/api/student/enrollments', methods=['GET'])
def get_student_enrollments():
    """R1 學生：查詢自己的選課紀錄"""
    user_info = get_current_user()
    if not user_info or user_info[1] != 'R1':
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    student_id = user_info[2].split(':')[1]  # 格式：student:S2020001
    
    db = get_db()
    cursor = db.execute("""
        SELECT e.enrollment_id, e.course_id, c.course_name, e.semester, e.grade,
               e.status, e.conflict_reason, e.enroll_date
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        WHERE e.student_id = ?
        ORDER BY e.semester DESC, e.course_id
    """, (student_id,))
    
    enrollments = [dict(row) for row in cursor.fetchall()]
    
    ch.log_action(db, username, 'R1', 'query', 'enrollment', None,
                 query_scope=f'student:{student_id}', result_count=len(enrollments))
    db.close()
    
    return jsonify(enrollments), 200


@app.route('/api/student/enroll', methods=['POST'])
def student_enroll():
    """R1 學生：提出選課申請"""
    user_info = get_current_user()
    if not user_info or user_info[1] != 'R1':
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    student_id = user_info[2].split(':')[1]
    
    data = request.get_json()
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'error': '課程 ID 不能為空'}), 400
    
    db = get_db()
    
    # 檢查課程是否存在
    cursor = db.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    if not cursor.fetchone():
        return jsonify({'error': '課程不存在'}), 404
    
    # 自動檢測衝突（混合型）
    conflict_reason = ch.auto_detect_conflicts(db, student_id, course_id)
    
    status = 'Conflict' if conflict_reason else 'Enrolled'
    
    try:
        db.execute("""
            INSERT INTO enrollments
            (student_id, course_id, semester, status, enroll_date, conflict_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, course_id, ch.CURRENT_SEMESTER, status, 
              datetime.now().strftime('%Y-%m-%d'), conflict_reason or ''))
        
        db.commit()
        
        ch.log_action(db, username, 'R1', 'enroll', 'enrollment', course_id,
                     query_scope=f'student:{student_id}', status='success')
        
        return jsonify({
            'message': '選課申請已提交',
            'status': status,
            'conflict_reason': conflict_reason,
        }), 201
    
    except Exception as e:
        ch.log_action(db, username, 'R1', 'enroll', 'enrollment', course_id,
                     status='error', error_message=str(e))
        return jsonify({'error': str(e)}), 400
    
    finally:
        db.close()


@app.route('/api/student/withdraw', methods=['POST'])
def student_withdraw():
    """R1 學生：退選課程（截止前）"""
    user_info = get_current_user()
    if not user_info or user_info[1] != 'R1':
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    student_id = user_info[2].split(':')[1]
    
    data = request.get_json()
    enrollment_id = data.get('enrollment_id')
    
    if not enrollment_id:
        return jsonify({'error': 'enrollment_id 不能為空'}), 400
    
    db = get_db()
    
    try:
        cursor = db.execute("""
            SELECT * FROM enrollments WHERE enrollment_id = ? AND student_id = ?
        """, (enrollment_id, student_id))
        
        enrollment = cursor.fetchone()
        if not enrollment:
            return jsonify({'error': '選課紀錄不存在'}), 404
        
        # 更新狀態為 Withdrawn
        db.execute("""
            UPDATE enrollments
            SET status = 'Withdrawn', withdraw_date = ?
            WHERE enrollment_id = ?
        """, (datetime.now().strftime('%Y-%m-%d'), enrollment_id))
        
        db.commit()
        
        ch.log_action(db, username, 'R1', 'withdraw', 'enrollment', enrollment_id,
                     status='success')
        
        return jsonify({'message': '已退選'}), 200
    
    except Exception as e:
        ch.log_action(db, username, 'R1', 'withdraw', 'enrollment', enrollment_id,
                     status='error', error_message=str(e))
        return jsonify({'error': str(e)}), 400
    
    finally:
        db.close()


# ==================== 教授查詢端點 ====================

@app.route('/api/professor/courses', methods=['GET'])
def get_professor_courses():
    """R2 教授：查詢自己教授的課程"""
    user_info = get_current_user()
    if not user_info or user_info[1] != 'R2':
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    prof_id = user_info[2].split(':')[1]  # 格式：professor:P000001
    
    db = get_db()
    cursor = db.execute("""
        SELECT * FROM courses WHERE instructor_id = ?
        ORDER BY semester DESC, course_id
    """, (prof_id,))
    
    courses = [dict(row) for row in cursor.fetchall()]
    
    ch.log_action(db, username, 'R2', 'query', 'course', None,
                 query_scope=f'professor:{prof_id}', result_count=len(courses))
    db.close()
    
    return jsonify(courses), 200


@app.route('/api/professor/roster/<course_id>', methods=['GET'])
def get_professor_roster(course_id: str):
    """R2 教授：查詢班級名單（含成績）"""
    user_info = get_current_user()
    if not user_info or user_info[1] != 'R2':
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    prof_id = user_info[2].split(':')[1]
    
    db = get_db()
    
    # 檢查該教授是否教這門課
    cursor = db.execute("""
        SELECT * FROM courses WHERE course_id = ? AND instructor_id = ?
    """, (course_id, prof_id))
    
    if not cursor.fetchone():
        ch.log_action(db, username, 'R2', 'query', 'enrollment', course_id,
                     status='denied', error_message='無權存取該課程')
        db.close()
        return jsonify({'error': '無權存取該課程'}), 403
    
    # 取得班級名單
    cursor = db.execute("""
        SELECT s.student_id, s.name, e.enrollment_id, e.grade, e.status
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        WHERE e.course_id = ? AND e.status IN ('Enrolled', 'Completed')
        ORDER BY s.student_id
    """, (course_id,))
    
    roster = [dict(row) for row in cursor.fetchall()]
    
    ch.log_action(db, username, 'R2', 'query', 'enrollment', course_id,
                 query_scope=f'course:{course_id}', result_count=len(roster))
    db.close()
    
    return jsonify(roster), 200


# ==================== 教務長/系主任查詢端點 ====================

@app.route('/api/admin/conflicts', methods=['GET'])
def get_conflicts():
    """R4 教務人員 / R5 管理員：查詢待審核的衝突選課"""
    user_info = get_current_user()
    if not user_info or user_info[1] not in ['R3', 'R4', 'R5']:
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    role = user_info[1]
    
    db = get_db()
    
    # R3 系主任只能看自己系的衝突
    if role == 'R3':
        dept = user_info[2].split(':')[1]
        cursor = db.execute("""
            SELECT e.enrollment_id, e.student_id, s.name, e.course_id, c.course_name,
                   e.conflict_reason, e.enroll_date
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.status = 'Conflict' AND s.major = ?
            ORDER BY e.enroll_date DESC
        """, (dept,))
    else:
        # R4/R5 可以看全校
        cursor = db.execute("""
            SELECT e.enrollment_id, e.student_id, s.name, e.course_id, c.course_name,
                   e.conflict_reason, e.enroll_date
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.status = 'Conflict'
            ORDER BY e.enroll_date DESC
        """)
    
    conflicts = [dict(row) for row in cursor.fetchall()]
    
    ch.log_action(db, username, role, 'query', 'enrollment', None,
                 query_scope='conflicts', result_count=len(conflicts))
    db.close()
    
    return jsonify(conflicts), 200


# ==================== 管理員端點 ====================

@app.route('/api/admin/import/students', methods=['POST'])
def admin_import_students():
    """R5 管理員：導入學生資料"""
    user_info = get_current_user()
    if not user_info or user_info[1] != 'R5':
        return jsonify({'error': '無權限存取'}), 403
    
    username = user_info[0]
    db = get_db()
    
    try:
        csv_path = COURSEHUB_DATA_DIR / 'students_history.csv'
        stats = ch.import_students_from_csv(db, csv_path, username)
        
        ch.log_action(db, username, 'R5', 'data_import', 'student', None,
                     status='success')
        
        return jsonify({
            'message': '學生資料導入完成',
            'stats': stats,
        }), 200
    
    except Exception as e:
        ch.log_action(db, username, 'R5', 'data_import', 'student', None,
                     status='error', error_message=str(e))
        return jsonify({'error': str(e)}), 400
    
    finally:
        db.close()


# ==================== 健康檢查 ====================

@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    return jsonify({'status': 'ok'}), 200


# ==================== 錯誤處理 ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '找不到該資源'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': '伺服器內部錯誤'}), 500


# ==================== CLI 命令 ====================

def main():
    parser = argparse.ArgumentParser(description='CourseHub API 服務')
    parser.add_argument('--create-admin', type=str, help='建立管理員帳號')
    parser.add_argument('--host', default='localhost', help='綁定主機')
    parser.add_argument('--port', type=int, default=5000, help='綁定埠口')
    parser.add_argument('--debug', action='store_true', help='除錯模式')
    
    args = parser.parse_args()
    
    # 初始化資料庫
    ch.initialize(COURSEHUB_DB_PATH)
    COURSEHUB_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 建立管理員
    if args.create_admin:
        db = get_db()
        username = args.create_admin
        password = input(f"請為 {username} 設定密碼：")
        
        salt, password_hash = ch.hash_password(password)
        
        try:
            db.execute("""
                INSERT INTO users (username, password_salt, password_hash, role, scope, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, salt, password_hash, 'R5', 'admin', 1, datetime.now().isoformat()))
            db.commit()
            print(f"✅ 管理員帳號 '{username}' 建立成功")
        except Exception as e:
            print(f"❌ 建立失敗：{e}")
        finally:
            db.close()
        
        return
    
    # 啟動伺服器
    print(f"🚀 CourseHub API 啟動中...")
    print(f"📍 http://{args.host}:{args.port}")
    print(f"💾 資料庫：{COURSEHUB_DB_PATH}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
