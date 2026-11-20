#!/usr/bin/env python3
"""
Generate complete CourseHub dataset matching the original system configuration.
配置: 12 departments, 2000 students, 192 courses, 3-year historical data
"""

import csv
import random
from datetime import datetime, timedelta
from collections import defaultdict

# Configuration (matching stored configuration)
DEPARTMENTS = [
    "計算機科學", "數學", "物理", "化學", "生物",
    "工程", "經濟", "管理", "法律", "文學",
    "歷史", "藝術"
]

DIFFICULTY_LEVELS = ["初級", "中級", "高級", "進階"]
SEMESTERS = ["春季", "秋季"]
YEARS = [2022, 2023, 2024]

def generate_students(n=2000):
    """生成學生數據"""
    students = []
    student_ids = set()
    
    for i in range(n):
        sid = f"S{i+1:06d}"
        student_ids.add(sid)
        department = random.choice(DEPARTMENTS)
        year = random.randint(1, 4)  # 大一到大四
        gpa = round(random.uniform(1.5, 4.0), 2)
        
        students.append({
            'student_id': sid,
            'name': f'Student_{i+1}',
            'department': department,
            'year': year,
            'gpa': gpa,
            'enrollment_date': (datetime.now() - timedelta(days=random.randint(365, 1095))).strftime('%Y-%m-%d')
        })
    
    return students, student_ids

def generate_courses(n=192):
    """生成課程數據"""
    courses = []
    course_ids = set()
    
    courses_per_dept = n // len(DEPARTMENTS)
    course_id_counter = 0
    
    for dept_idx, dept in enumerate(DEPARTMENTS):
        for i in range(courses_per_dept):
            cid = f"C{course_id_counter:04d}"
            course_ids.add(cid)
            
            courses.append({
                'course_id': cid,
                'name': f'{dept}_Course_{i+1}',
                'department': dept,
                'credits': random.choice([3, 4, 6]),
                'capacity': random.randint(20, 100),
                'difficulty': random.choice(DIFFICULTY_LEVELS),
                'description': f'Course {cid} in {dept}'
            })
            course_id_counter += 1
    
    return courses, course_ids, course_id_counter

def generate_enrollments(students, courses, student_ids, course_ids, base_count=22873):
    """生成註冊數據"""
    enrollments = []
    enrollment_id = 0
    
    # 目標: 22,873 條記錄
    target_enrollments_per_student = base_count // len(students)
    
    for student in students:
        sid = student['student_id']
        student_year = student['year']
        
        # 每個學生選 10-12 門課程
        num_courses = random.randint(10, 12)
        selected_courses = random.sample(list(course_ids), min(num_courses, len(course_ids)))
        
        for cid in selected_courses:
            for year in random.sample(YEARS, random.randint(1, 2)):  # 在 2-3 年內註冊
                semester = random.choice(SEMESTERS)
                
                enrollments.append({
                    'enrollment_id': f'E{enrollment_id:08d}',
                    'student_id': sid,
                    'course_id': cid,
                    'year': year,
                    'semester': semester,
                    'grade': random.choice(['A', 'B+', 'B', 'C+', 'C', 'D', 'F', None]),
                    'status': random.choice(['completed', 'enrolled', 'dropped']),
                    'enrollment_date': (datetime(year, 1 if semester == "春季" else 9, 1) + timedelta(days=random.randint(0, 10))).strftime('%Y-%m-%d')
                })
                enrollment_id += 1
    
    return enrollments[:base_count]  # 確保正好是目標數量

def generate_prerequisites(courses, course_id_list):
    """生成先修課程數據"""
    prerequisites = []
    prereq_id = 0
    
    # 創建課程序列 - 只有高級課程需要先修
    course_dict = {c['course_id']: c for c in courses}
    
    # 20% 的課程有先修要求
    for course in random.sample(courses, int(len(courses) * 0.2)):
        if course['difficulty'] in ['中級', '高級', '進階']:
            # 找到同部門的低級課程作為先修
            dept_courses = [c for c in courses 
                          if c['department'] == course['department'] 
                          and c['course_id'] != course['course_id']
                          and c['difficulty'] in ['初級', '中級']]
            
            if dept_courses:
                prereq = random.choice(dept_courses)
                prerequisites.append({
                    'prerequisite_id': f'P{prereq_id:06d}',
                    'course_id': course['course_id'],
                    'prerequisite_course_id': prereq['course_id'],
                    'is_required': random.choice([True, False])
                })
                prereq_id += 1
    
    return prerequisites

def write_csv(data, filename, fieldnames):
    """寫入 CSV 文件"""
    filepath = f"C:/Users/s1015/OneDrive/桌面/CourseHub/{filename}"
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ 已生成: {filename} ({len(data)} 條記錄)")

def main():
    print("🔄 正在生成 CourseHub 數據集...\n")
    
    # 生成數據
    print("生成學生數據...")
    students, student_ids = generate_students(2000)
    
    print("生成課程數據...")
    courses, course_ids, course_id_count = generate_courses(192)
    
    print("生成註冊數據...")
    enrollments = generate_enrollments(students, courses, student_ids, course_ids, 22873)
    
    print("生成先修課程數據...")
    prerequisites = generate_prerequisites(courses, list(course_ids))
    
    # 寫入 CSV 文件
    print("\n📝 寫入 CSV 文件...\n")
    
    write_csv(students, 'students.csv', 
              ['student_id', 'name', 'department', 'year', 'gpa', 'enrollment_date'])
    
    write_csv(courses, 'courses.csv',
              ['course_id', 'name', 'department', 'credits', 'capacity', 'difficulty', 'description'])
    
    write_csv(enrollments, 'enrollments.csv',
              ['enrollment_id', 'student_id', 'course_id', 'year', 'semester', 'grade', 'status', 'enrollment_date'])
    
    write_csv(prerequisites, 'prerequisites.csv',
              ['prerequisite_id', 'course_id', 'prerequisite_course_id', 'is_required'])
    
    # 統計
    print("\n" + "="*50)
    print("📊 數據集統計:")
    print("="*50)
    print(f"  學生數: {len(students)}")
    print(f"  課程數: {len(courses)}")
    print(f"  註冊記錄: {len(enrollments)}")
    print(f"  先修要求: {len(prerequisites)}")
    print(f"  總記錄數: {len(students) + len(courses) + len(enrollments) + len(prerequisites)}")
    print("="*50)
    print("\n✅ 數據生成完成！")

if __name__ == '__main__':
    main()
