"""
CourseHub RAG + LLM System
完全本地運行，免費開源

依賴: Ollama (本地 LLM)
所有其他功能用純 Python 實現
"""

import json
import sqlite3
import requests
import hashlib
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
from collections import defaultdict

# ============================================================================
# 第一部分: 簡易向量化模塊 (不依賴外部庫)
# ============================================================================

class SimpleVectorizer:
    """簡單的向量化器 - 基於 TF-IDF 和關鍵字匹配"""
    
    def __init__(self):
        self.vocabulary = set()
        self.documents = {}
        
    def _tokenize(self, text: str) -> List[str]:
        """簡單分詞"""
        # 轉小寫，移除特殊字符，分割
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return tokens
    
    def _calculate_vector(self, text: str) -> Dict[str, float]:
        """計算文本的稀疏向量表示"""
        tokens = self._tokenize(text)
        self.vocabulary.update(tokens)
        
        vector = defaultdict(float)
        for token in tokens:
            vector[token] += 1.0
        
        # 正規化
        norm = sum(v**2 for v in vector.values()) ** 0.5
        if norm > 0:
            vector = {k: v/norm for k, v in vector.items()}
        
        return dict(vector)
    
    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """添加文檔"""
        vector = self._calculate_vector(text)
        self.documents[doc_id] = {
            'vector': vector,
            'text': text,
            'metadata': metadata or {}
        }
    
    def similarity(self, vec1: Dict, vec2: Dict) -> float:
        """計算兩個向量的餘弦相似度"""
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) 
                         for k in set(vec1.keys()) | set(vec2.keys()))
        return dot_product
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """搜索相似文檔"""
        query_vector = self._calculate_vector(query)
        
        scores = []
        for doc_id, doc_data in self.documents.items():
            score = self.similarity(query_vector, doc_data['vector'])
            scores.append((doc_id, score, doc_data['metadata']))
        
        # 按相似度排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================================
# 第二部分: RAG 檢索模塊
# ============================================================================

class CourseHubRAG:
    """CourseHub 的 RAG 檢索系統"""
    
    def __init__(self, coursehub_dir: str):
        self.coursehub_dir = Path(coursehub_dir)
        self.vectorizer = SimpleVectorizer()
        self.courses_data = {}
        self.students_data = {}
        self.prerequisites_data = {}
        self.enrollments_data = {}
        
        # 初始化索引
        self._load_and_index_data()
    
    def _load_and_index_data(self):
        """從 CSV 加載並索引所有資料"""
        print("📊 正在加載和索引 CourseHub 資料...")
        
        # 加載課程
        courses_file = self.coursehub_dir / "data" / "courses_active.csv"
        if courses_file.exists():
            with open(courses_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    course_id = row['course_id']
                    self.courses_data[course_id] = row
                    
                    # 索引課程信息
                    course_text = f"{row.get('course_name', '')} {row.get('description', '')} {row.get('department', '')}"
                    self.vectorizer.add_document(
                        f"course_{course_id}",
                        course_text,
                        {'type': 'course', 'course_id': course_id, 'data': row}
                    )
        
        # 加載學生
        students_file = self.coursehub_dir / "data" / "students_history.csv"
        if students_file.exists():
            with open(students_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    student_id = row['student_id']
                    self.students_data[student_id] = row
        
        # 加載先修課程
        prereqs_file = self.coursehub_dir / "data" / "prerequisites.csv"
        if prereqs_file.exists():
            with open(prereqs_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    course_id = row['course_id']
                    if course_id not in self.prerequisites_data:
                        self.prerequisites_data[course_id] = []
                    self.prerequisites_data[course_id].append(row)
        
        print(f"✅ 已加載: {len(self.courses_data)} 個課程, {len(self.students_data)} 個學生")
    
    def search_courses(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索相關課程"""
        results = self.vectorizer.search(query, top_k=top_k)
        
        output = []
        for doc_id, score, metadata in results:
            if metadata.get('type') == 'course':
                course_data = metadata.get('data', {})
                output.append({
                    'course_id': metadata['course_id'],
                    'course_name': course_data.get('course_name', ''),
                    'description': course_data.get('description', ''),
                    'department': course_data.get('department', ''),
                    'instructor': course_data.get('instructor', ''),
                    'time_slots': course_data.get('time_slots', ''),
                    'capacity': course_data.get('capacity', 0),
                    'relevance_score': f"{score:.2%}"
                })
        
        return output
    
    def get_student_profile(self, student_id: str) -> Dict:
        """獲取學生檔案"""
        return self.students_data.get(student_id, {})
    
    def get_course_prerequisites(self, course_id: str) -> List[Dict]:
        """獲取課程的先修要求"""
        return self.prerequisites_data.get(course_id, [])
    
    def get_course_details(self, course_id: str) -> Dict:
        """獲取課程詳細信息"""
        return self.courses_data.get(course_id, {})


# ============================================================================
# 第三部分: Ollama LLM 集成
# ============================================================================

class OllamaLLM:
    """Ollama 本地 LLM 集成"""
    
    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.conversation_history = []
    
    def check_connection(self) -> bool:
        """檢查 Ollama 服務是否運行"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """生成文本"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                return f"❌ 錯誤: {response.status_code}"
        except Exception as e:
            return f"❌ 連接失敗: {str(e)}"
    
    def chat(self, user_message: str, system_prompt: str = "") -> str:
        """聊天模式"""
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # 構建完整的提示詞
        full_prompt = system_prompt + "\n\n"
        for msg in self.conversation_history[-5:]:  # 保持最後 5 條消息的上下文
            full_prompt += f"{msg['role'].upper()}: {msg['content']}\n"
        full_prompt += "ASSISTANT:"
        
        response = self.generate(full_prompt)
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        return response
    
    def clear_history(self):
        """清除對話歷史"""
        self.conversation_history = []


# ============================================================================
# 第四部分: RAG + LLM 管道
# ============================================================================

class CourseHubAssistant:
    """CourseHub 智能助理 - 結合 RAG + LLM"""
    
    def __init__(self, coursehub_dir: str, model_name: str = "mistral"):
        self.rag = CourseHubRAG(coursehub_dir)
        self.llm = OllamaLLM(model_name=model_name)
        
        self.system_prompt = """你是一個專業的大學選課助理。你的工作是幫助學生：
1. 找到合適的課程
2. 解決選課衝突
3. 規劃學習路徑
4. 回答選課相關問題

使用提供的課程信息和學生檔案，給出個性化的建議。
始終考慮：時間衝突、先修要求、課程容量、學生的興趣和能力。

回應要簡潔、友善、實用。"""
    
    def answer_question(self, student_id: str, question: str) -> Dict[str, Any]:
        """回答學生的選課問題"""
        
        # 第 1 步: RAG 檢索相關信息
        print(f"\n🔍 正在檢索相關信息...")
        course_results = self.rag.search_courses(question, top_k=5)
        student_profile = self.rag.get_student_profile(student_id)
        
        # 第 2 步: 構建上下文
        context = f"""
學生信息：
- ID: {student_id}
- 年級: {student_profile.get('year', 'N/A')}
- 專業: {student_profile.get('major', 'N/A')}
- GPA: {student_profile.get('gpa', 'N/A')}

相關課程：
"""
        for i, course in enumerate(course_results, 1):
            context += f"""
{i}. {course['course_name']} ({course['course_id']})
   - 系別: {course['department']}
   - 教師: {course['instructor']}
   - 時間: {course['time_slots']}
   - 容量: {course['capacity']}
   - 相關度: {course['relevance_score']}"""
        
        context += "\n"
        
        # 第 3 步: 用 LLM 生成回答
        print("🤖 正在生成智能回答...")
        full_prompt = f"""{self.system_prompt}

{context}

學生問題: {question}

請基於上述信息，提供詳細且實用的建議："""
        
        response = self.llm.generate(full_prompt, temperature=0.7, max_tokens=800)
        
        return {
            'student_id': student_id,
            'question': question,
            'retrieved_courses': course_results,
            'student_profile': student_profile,
            'assistant_response': response,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_course_plan(self, student_id: str, goal: str) -> Dict[str, Any]:
        """為學生生成學習計劃"""
        
        student_profile = self.rag.get_student_profile(student_id)
        
        prompt = f"""{self.system_prompt}

為以下學生設計詳細的學習計劃：
- 學生 ID: {student_id}
- 年級: {student_profile.get('year', 'N/A')}
- 專業: {student_profile.get('major', 'N/A')}
- 目標: {goal}

請提供：
1. 核心課程建議
2. 選修課程建議
3. 學期規劃
4. 先修課程檢查

"""
        
        response = self.llm.generate(prompt, temperature=0.7, max_tokens=1000)
        
        return {
            'student_id': student_id,
            'goal': goal,
            'plan': response,
            'timestamp': datetime.now().isoformat()
        }
    
    def resolve_conflict(self, student_id: str, conflict_description: str) -> Dict[str, Any]:
        """解決選課衝突"""
        
        prompt = f"""{self.system_prompt}

學生 {student_id} 遇到了選課問題：
{conflict_description}

請分析問題並提供解決方案，包括：
1. 問題分析
2. 可能的解決方案
3. 每個方案的優缺點
4. 推薦方案

"""
        
        response = self.llm.generate(prompt, temperature=0.7, max_tokens=800)
        
        return {
            'student_id': student_id,
            'conflict': conflict_description,
            'resolution': response,
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🎓 CourseHub RAG + LLM 系統")
    print("="*60)
    
    coursehub_path = r"C:\Users\s1015\OneDrive\桌面\CourseHub"
    
    # 初始化助理
    print("\n📚 初始化 CourseHub 助理...")
    assistant = CourseHubAssistant(coursehub_path, model_name="mistral")
    
    # 檢查 Ollama 連接
    print("\n🔗 檢查 Ollama 服務...")
    if assistant.llm.check_connection():
        print("✅ Ollama 已連接")
    else:
        print("❌ Ollama 未運行 - 請先安裝並運行 Ollama")
        print("   下載地址: https://ollama.ai")
        print("   安裝後運行: ollama pull mistral")
        exit(1)
    
    # 測試用例
    test_cases = [
        ("S2020001", "我想學習機器學習相關課程，但時間要靈活"),
        ("S2020002", "我有時間衝突，該怎麼辦？"),
    ]
    
    print("\n" + "="*60)
    print("🧪 測試案例")
    print("="*60)
    
    for student_id, question in test_cases:
        print(f"\n【學生 {student_id}】")
        print(f"問題: {question}")
        result = assistant.answer_question(student_id, question)
        print(f"\n回答:\n{result['assistant_response']}")
        print("-" * 60)
