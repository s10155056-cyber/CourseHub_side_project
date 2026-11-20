#!/usr/bin/env python3
"""
CourseHub 數據集生成腳本

生成 3 學年（2024-2026）的課程、學生和選課紀錄
包括時間衝突、先修課程、容量超額等真實情況
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

# ==================== 常數定義 ====================

DEPARTMENTS = {
    'EE': '電機系',
    'CE': '電子系',
    'CS': '資訊系',
    'ME': '機械系',
    'CH': '化工系',
    'CV': '土木系',
    'BIO': '生物系',
    'CHEM': '化學系',
    'PHY': '物理系',
    'MATH': '數學系',
    'BUS': '商學系',
    'MUS': '音樂系',
}

STUDENT_COUNT = 2000
COURSES_PER_DEPT = 17  # 平均每系 17 門課
SEMESTERS = ['2024F', '2025S', '2025F', '2026S', '2026F']  # 三學年五學期

GRADE_DISTRIBUTION = {
    'A': 0.15,
    'B+': 0.15,
    'B': 0.25,
    'C+': 0.15,
    'C': 0.15,
    'D': 0.10,
    'F': 0.05,
}

GRADE_POINTS = {
    'A': 4.0,
    'B+': 3.7,
    'B': 3.3,
    'C+': 3.0,
    'C': 2.7,
    'D': 2.3,
    'F': 0.0,
}

WITHDRAWAL_RATE = 0.05  # 5% 選課後退選
TIME_CONFLICT_RATE = 0.03  # 3% 會因時間衝突被標記
CAPACITY_EXCEED_RATE = 0.02  # 2% 會因人數超額被標記

# ==================== 輔助函數 ====================

def generate_student_id(index: int) -> str:
    """生成學號 S + 7位數字"""
    return f"S{2020000 + index:07d}"

def generate_course_id(index: int) -> str:
    """生成課程編號 C + 6位數字"""
    return f"C{index:06d}"

def generate_time_slots() -> str:
    """生成課程時間表 (JSON 格式)"""
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    hours = [(9, 11), (11, 13), (14, 16), (16, 18)]
    
    # 隨機選擇 1-2 天課
    num_days = random.randint(1, 2)
    selected_days = random.sample(days, num_days)
    start_hour, end_hour = random.choice(hours)
    
    slots = [
        {
            "day": day,
            "start": f"{start_hour:02d}:00",
            "end": f"{end_hour:02d}:00"
        }
        for day in selected_days
    ]
    return json.dumps(slots, ensure_ascii=False)

def check_time_overlap(slots1: str, slots2: str) -> bool:
    """檢查兩個時間表是否有重疊"""
    try:
        s1 = json.loads(slots1)
        s2 = json.loads(slots2)
        
        for slot1 in s1:
            for slot2 in s2:
                if slot1['day'] == slot2['day']:
                    # 比較時間範圍
                    start1 = int(slot1['start'].split(':')[0])
                    end1 = int(slot1['end'].split(':')[0])
                    start2 = int(slot2['start'].split(':')[0])
                    end2 = int(slot2['end'].split(':')[0])
                    
                    if (start1 < end2) and (start2 < end1):
                        return True
        return False
    except:
        return False

def generate_name(gender: str) -> str:
    """隨機生成中文名字"""
    first_names_m = ['王', '李', '張', '劉', '陳', '楊', '黃', '吳', '周', '徐']
    first_names_f = ['王', '李', '張', '劉', '陳', '楊', '黃', '吳', '周', '徐']
    last_names = ['小明', '大衛', '子軒', '欣妤', '美玲', '文傑', '詩涵', '宗翰', '昱伊', '品妤']
    
    first = random.choice(first_names_m if gender == 'M' else first_names_f)
    last = random.choice(last_names)
    return f"{first}{last}"

# ==================== 生成課程資料 ====================

def generate_courses() -> List[Dict]:
    """生成 200+ 門課程"""
    courses = []
    course_idx = 1
    
    instructors = [(f"P{i:06d}", f"教授{i}") for i in range(1, 100)]
    
    for dept_code in DEPARTMENTS.keys():
        for course_level in [100, 200, 300, 400]:
            for course_num in range(1, 5):  # 每級別 4 門課
                course_id = generate_course_id(course_idx)
                course_idx += 1
                
                course_name = f"{DEPARTMENTS[dept_code]}課程-{course_level//100}年級-{course_num}"
                instructor_id, instructor_name = random.choice(instructors)
                
                # 決定開課學期（不是每學期都開）
                semester = random.choice(SEMESTERS[2:])  # 從 2025F 開始
                
                courses.append({
                    'CourseID': course_id,
                    'CourseName': course_name,
                    'Department': dept_code,
                    'Credits': random.randint(1, 4),
                    'Capacity': random.randint(30, 80),
                    'Semester': semester,
                    'InstructorID': instructor_id,
                    'InstructorName': instructor_name,
                    'TimeSlots': generate_time_slots(),
                    'ClassRoom': f"{dept_code}-{random.randint(101, 410)}",
                    'Prerequisites': '',  # 先修課程稍後設定
                    'CourseLevel': course_level,
                    'IsElective': random.choice(['Y', 'N']),
                    'IsCompulsory': random.choice(['Y', 'N']),
                })
    
    return courses

# ==================== 生成學生資料 ====================

def generate_students() -> List[Dict]:
    """生成 2000 名學生"""
    students = []
    
    for i in range(STUDENT_COUNT):
        student_id = generate_student_id(i)
        dept = random.choice(list(DEPARTMENTS.keys()))
        gender = random.choice(['M', 'F'])
        
        # 入學年份分布：40% 大一、30% 大二、20% 大三、10% 大四
        enrollment_year = random.choices(
            [2026, 2025, 2024, 2023],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        
        grad_year = enrollment_year + 4
        
        # 計算學籍狀態
        if grad_year < 2026:
            status = 'Graduated'
        elif enrollment_year == 2026 and random.random() < 0.02:
            status = random.choice(['Withdrawn', 'On_Leave'])
        else:
            status = 'Active'
        
        students.append({
            'StudentID': student_id,
            'Name': generate_name(gender),
            'Major': dept,
            'GradYear': grad_year,
            'EnrollmentYear': enrollment_year,
            'StudentStatus': status,
            'CurrentGPA': round(random.uniform(2.0, 4.0), 2),
            'CompletedCredits': random.randint(0, 120) if status == 'Active' else random.randint(60, 128),
            'TotalCreditsRequired': 128,
        })
    
    return students

# ==================== 生成選課紀錄 ====================

def generate_enrollments(courses: List[Dict], students: List[Dict]) -> List[Dict]:
    """生成選課紀錄（含衝突和退選）"""
    enrollments = []
    enrollment_id = 1
    
    for student in students:
        if student['StudentStatus'] != 'Active':
            continue
        
        # 計算學生應該選過的學期
        enrollment_year = student['EnrollmentYear']
        available_semesters = [s for s in SEMESTERS if int(s[:4]) >= enrollment_year]
        
        # 隨機選擇每個學期選幾門課（通常 4-7 門）
        for semester in available_semesters:
            if random.random() < 0.05:  # 有些學期不選課
                continue
            
            num_courses = random.randint(4, 7)
            dept_courses = [c for c in courses if c['Department'] == student['Major'] and c['Semester'] == semester]
            
            if not dept_courses:
                continue
            
            selected_courses = random.sample(dept_courses, min(num_courses, len(dept_courses)))
            
            # 檢測時間衝突
            enrolled_courses = []
            for course in selected_courses:
                has_conflict = False
                
                # 與已選課程比較
                for enrolled_course in enrolled_courses:
                    if check_time_overlap(course['TimeSlots'], enrolled_course['TimeSlots']):
                        has_conflict = True
                        break
                
                # 隨機產生衝突
                if random.random() < TIME_CONFLICT_RATE and not has_conflict:
                    has_conflict = True
                
                # 容量超額
                conflict_reason = None
                if has_conflict:
                    conflict_reason = 'TimeConflict'
                elif random.random() < CAPACITY_EXCEED_RATE:
                    conflict_reason = 'CapacityExceeded'
                
                status = 'Conflict' if conflict_reason else 'Enrolled'
                
                # 決定是否有成績
                grade = None
                grade_point = None
                if random.random() < 0.7:  # 70% 有成績
                    grade = random.choices(list(GRADE_POINTS.keys()), 
                                         weights=[GRADE_DISTRIBUTION[g] for g in GRADE_POINTS.keys()])[0]
                    grade_point = GRADE_POINTS[grade]
                    status = 'Completed' if status == 'Enrolled' else status
                
                # 決定是否退選
                withdraw_date = None
                if status == 'Enrolled' and random.random() < WITHDRAWAL_RATE:
                    status = 'Withdrawn'
                    enroll_date = datetime.strptime(f"{semester[0:4]}-", "%Y-").replace(month=9 if semester.endswith('F') else 2)
                    withdraw_date = (enroll_date + timedelta(days=random.randint(7, 45))).strftime('%Y-%m-%d')
                
                enroll_date = datetime.strptime(f"{semester[0:4]}-", "%Y-").replace(month=9 if semester.endswith('F') else 2)
                
                enrollments.append({
                    'EnrollmentID': enrollment_id,
                    'StudentID': student['StudentID'],
                    'CourseID': course['CourseID'],
                    'Semester': semester,
                    'Grade': grade or '',
                    'GradePoint': grade_point or '',
                    'Status': status,
                    'EnrollDate': enroll_date.strftime('%Y-%m-%d'),
                    'WithdrawDate': withdraw_date or '',
                    'ConflictReason': conflict_reason or '',
                    'ReviewedBy': random.choice(['', 'A000001', 'A000002']) if conflict_reason else '',
                    'ReviewedDate': (datetime.strptime(enroll_date.strftime('%Y-%m-%d'), '%Y-%m-%d') + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d') if conflict_reason and random.random() < 0.6 else '',
                })
                
                enrollment_id += 1
                enrolled_courses.append(course)
    
    return enrollments

# ==================== 生成先修課程 ====================

def generate_prerequisites(courses: List[Dict]) -> List[Dict]:
    """生成先修課程關係"""
    prerequisites = []
    
    for dept_code in DEPARTMENTS.keys():
        dept_courses = [c for c in courses if c['Department'] == dept_code]
        
        for course in dept_courses:
            # 300 級以上的課程有先修
            if course['CourseLevel'] >= 300:
                level_100_courses = [c for c in dept_courses if c['CourseLevel'] == 100]
                level_200_courses = [c for c in dept_courses if c['CourseLevel'] == 200]
                
                prereq_sources = level_100_courses + level_200_courses
                
                if prereq_sources:
                    # 隨機選 1-2 門先修課程
                    num_prereqs = random.randint(1, min(2, len(prereq_sources)))
                    prereq_courses = random.sample(prereq_sources, num_prereqs)
                    
                    for prereq in prereq_courses:
                        prerequisites.append({
                            'CourseID': course['CourseID'],
                            'PrerequisiteCourseID': prereq['CourseID'],
                            'IsStrict': random.choice(['Y', 'N']),
                        })
    
    return prerequisites

# ==================== 主生成函數 ====================

def generate_all_data(output_dir: Path):
    """生成所有數據並寫入 CSV"""
    output_dir.mkdir(exist_ok=True)
    
    print("📊 正在生成課程資料...")
    courses = generate_courses()
    print(f"✅ 生成了 {len(courses)} 門課程")
    
    print("👥 正在生成學生資料...")
    students = generate_students()
    print(f"✅ 生成了 {len(students)} 名學生")
    
    print("📝 正在生成選課紀錄...")
    enrollments = generate_enrollments(courses, students)
    print(f"✅ 生成了 {len(enrollments)} 筆選課紀錄")
    
    print("🔗 正在生成先修課程...")
    prerequisites = generate_prerequisites(courses)
    print(f"✅ 生成了 {len(prerequisites)} 條先修關係")
    
    # 寫入 CSV
    print("\n💾 正在寫入 CSV 檔案...")
    
    # 學生資料
    with open(output_dir / 'students_history.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=students[0].keys())
        writer.writeheader()
        writer.writerows(students)
    print(f"✅ 寫入 {output_dir / 'students_history.csv'}")
    
    # 課程資料
    with open(output_dir / 'courses_active.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=courses[0].keys())
        writer.writeheader()
        writer.writerows(courses)
    print(f"✅ 寫入 {output_dir / 'courses_active.csv'}")
    
    # 選課紀錄
    with open(output_dir / 'enrollments_history.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=enrollments[0].keys())
        writer.writeheader()
        writer.writerows(enrollments)
    print(f"✅ 寫入 {output_dir / 'enrollments_history.csv'}")
    
    # 先修課程
    with open(output_dir / 'prerequisites.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=prerequisites[0].keys())
        writer.writeheader()
        writer.writerows(prerequisites)
    print(f"✅ 寫入 {output_dir / 'prerequisites.csv'}")
    
    print("\n🎉 資料生成完成！")

if __name__ == '__main__':
    output_dir = Path(__file__).parent / 'data'
    generate_all_data(output_dir)
