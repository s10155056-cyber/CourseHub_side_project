"""
CourseHub RAG + LLM - Streamlit 前端界面
完全本地運行，零成本的 AI 驅動課程助理
"""

import streamlit as st
from pathlib import Path
import sys
import json
from datetime import datetime

# 添加 CourseHub 目錄到 Python 路徑
coursehub_dir = r"C:\Users\s1015\OneDrive\桌面\CourseHub"
sys.path.insert(0, coursehub_dir)

# 導入 RAG 系統
from rag_system import CourseHubAssistant

# ============================================================================
# Streamlit 配置
# ============================================================================

st.set_page_config(
    page_title="🎓 CourseHub 智能選課助理",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: bold;
    }
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 初始化會話狀態
# ============================================================================

if 'assistant' not in st.session_state:
    st.session_state.assistant = None
    st.session_state.connected = False
    st.session_state.student_id = "S2020001"
    st.session_state.chat_history = []

# ============================================================================
# 頁面標題
# ============================================================================

st.markdown("""
<div class="header-container">
    <h1>🎓 CourseHub 智能選課助理</h1>
    <p>AI 驅動的個性化課程推薦系統 | 完全本地運行 | 零成本</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# 側邊欄
# ============================================================================

with st.sidebar:
    st.markdown("### ⚙️ 系統設置")
    
    # 初始化系統
    if st.button("🔌 連接 Ollama", use_container_width=True, type="primary"):
        with st.spinner("正在連接 Ollama 服務..."):
            try:
                st.session_state.assistant = CourseHubAssistant(
                    coursehub_dir, 
                    model_name="mistral"
                )
                
                if st.session_state.assistant.llm.check_connection():
                    st.session_state.connected = True
                    st.success("✅ Ollama 已連接")
                else:
                    st.error("❌ Ollama 未運行\n\n請先安裝並啟動 Ollama：\nhttps://ollama.ai")
            except Exception as e:
                st.error(f"❌ 連接失敗: {str(e)}")
    
    st.divider()
    
    # 學生選擇
    st.markdown("### 👤 學生信息")
    student_id = st.text_input("學生 ID", value=st.session_state.student_id)
    st.session_state.student_id = student_id
    
    st.divider()
    
    # 模型選擇
    st.markdown("### 🤖 LLM 模型選擇")
    model_choice = st.radio(
        "選擇模型",
        ["Mistral (快速)", "LLaMA 2 (強大)", "Neural Chat (對話優化)"],
        index=0
    )
    
    model_mapping = {
        "Mistral (快速)": "mistral",
        "LLaMA 2 (強大)": "llama2",
        "Neural Chat (對話優化)": "neural-chat"
    }
    
    st.divider()
    
    # 系統狀態
    st.markdown("### 📊 系統狀態")
    
    if st.session_state.connected:
        st.success("✅ 已連接")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("狀態", "在線")
        with col2:
            st.metric("模型", model_choice.split("(")[0].strip())
    else:
        st.warning("⚠️ 未連接\n\n請點擊「連接 Ollama」按鈕")
    
    st.divider()
    
    # 清除對話歷史
    if st.button("🗑️ 清除對話歷史", use_container_width=True):
        st.session_state.chat_history = []
        if st.session_state.assistant:
            st.session_state.assistant.llm.clear_history()
        st.success("✅ 已清除")

# ============================================================================
# 主要內容區域
# ============================================================================

if not st.session_state.connected:
    st.markdown("""
    <div class="error-box">
    <h3>🔌 未連接 Ollama</h3>
    <p>請在左邊欄點擊「連接 Ollama」按鈕連接本地 LLM 服務。</p>
    <p>如果 Ollama 未安裝，請先：</p>
    <ol>
        <li>下載 Ollama: https://ollama.ai</li>
        <li>安裝並啟動</li>
        <li>下載模型: <code>ollama pull mistral</code></li>
        <li>刷新此頁面</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

else:
    # 標籤頁
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 智能問答",
        "📚 課程推薦",
        "🎯 學習計劃",
        "⚔️ 衝突解決",
        "📖 幫助指南"
    ])
    
    # ========================================================================
    # 標籤頁 1: 智能問答
    # ========================================================================
    with tab1:
        st.markdown("### 💬 向 AI 助理提問")
        st.markdown("""
        <div class="info-box">
        <strong>💡 提示:</strong> 你可以問任何關於選課的問題，AI 會根據課程資料和你的檔案提供個性化建議。
        </div>
        """, unsafe_allow_html=True)
        
        question = st.text_area(
            "請輸入你的問題",
            placeholder="例如：我想學習機器學習相關課程，但時間要靈活...",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_q = st.button("🚀 提交問題", use_container_width=True, type="primary")
        
        if submit_q and question:
            with st.spinner("🤔 AI 正在思考..."):
                result = st.session_state.assistant.answer_question(
                    st.session_state.student_id,
                    question
                )
            
            # 顯示檢索到的課程
            st.markdown("#### 📚 相關課程")
            for i, course in enumerate(result['retrieved_courses'], 1):
                with st.expander(f"{i}. {course['course_name']} ({course['course_id']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**系別:** {course['department']}")
                        st.write(f"**教師:** {course['instructor']}")
                    with col2:
                        st.write(f"**時間:** {course['time_slots']}")
                        st.write(f"**容量:** {course['capacity']}")
                    st.write(f"**描述:** {course['description'][:200]}...")
                    st.write(f"*相關度: {course['relevance_score']}*")
            
            # 顯示 AI 回答
            st.markdown("#### 🤖 AI 助理的建議")
            st.markdown(f"""
            <div class="success-box">
            {result['assistant_response']}
            </div>
            """, unsafe_allow_html=True)
            
            # 保存到對話歷史
            st.session_state.chat_history.append({
                'type': 'question',
                'question': question,
                'response': result['assistant_response'],
                'timestamp': datetime.now().isoformat()
            })
    
    # ========================================================================
    # 標籤頁 2: 課程推薦
    # ========================================================================
    with tab2:
        st.markdown("### 📚 課程推薦")
        st.markdown("""
        <div class="info-box">
        <strong>🎯 功能:</strong> 基於你的興趣和學習目標，AI 會推薦最適合的課程組合。
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            interest = st.text_input(
                "你感興趣的領域",
                placeholder="例如：人工智能、數據科學、Web開發..."
            )
        
        with col2:
            difficulty = st.select_slider(
                "難度偏好",
                options=["入門", "基礎", "中等", "進階", "高級"]
            )
        
        if st.button("🔍 推薦課程", use_container_width=True, type="primary"):
            with st.spinner("⏳ 正在生成推薦..."):
                prompt = f"推薦 {interest} 領域的 {difficulty} 難度課程組合"
                result = st.session_state.assistant.answer_question(
                    st.session_state.student_id,
                    prompt
                )
            
            st.markdown("#### 推薦課程")
            for course in result['retrieved_courses'][:3]:
                with st.expander(f"✅ {course['course_name']}"):
                    st.write(f"**課程代號:** {course['course_id']}")
                    st.write(f"**系別:** {course['department']}")
                    st.write(f"**教師:** {course['instructor']}")
                    st.write(f"**時間:** {course['time_slots']}")
                    st.write(f"**容量:** {course['capacity']}")
            
            st.markdown("#### 📊 推薦理由")
            st.markdown(result['assistant_response'])
    
    # ========================================================================
    # 標籤頁 3: 學習計劃
    # ========================================================================
    with tab3:
        st.markdown("### 🎯 個性化學習計劃")
        st.markdown("""
        <div class="info-box">
        <strong>📋 說明:</strong> AI 會根據你的目標生成完整的學習路徑，包括課程序列、先修要求等。
        </div>
        """, unsafe_allow_html=True)
        
        goal = st.text_area(
            "你的學習目標",
            placeholder="例如：成為 AI 工程師、掌握數據分析技能、學習全棧開發...",
            height=80
        )
        
        semesters = st.slider("規劃的學期數", 1, 8, 4)
        
        if st.button("📋 生成計劃", use_container_width=True, type="primary"):
            with st.spinner("✍️ 正在生成學習計劃..."):
                result = st.session_state.assistant.generate_course_plan(
                    st.session_state.student_id,
                    goal
                )
            
            st.markdown("#### 🎯 你的學習路徑")
            st.markdown(f"""
            <div class="success-box">
            {result['plan']}
            </div>
            """, unsafe_allow_html=True)
            
            # 導出功能
            with st.expander("💾 導出計劃"):
                plan_json = json.dumps(result, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 下載為 JSON",
                    data=plan_json,
                    file_name="learning_plan.json",
                    mime="application/json"
                )
    
    # ========================================================================
    # 標籤頁 4: 衝突解決
    # ========================================================================
    with tab4:
        st.markdown("### ⚔️ 智能衝突解決")
        st.markdown("""
        <div class="info-box">
        <strong>⚡ 幫助:</strong> 當遇到選課衝突時，AI 會分析問題並提供最佳解決方案。
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            conflict_type = st.radio(
                "衝突類型",
                ["時間衝突", "先修課程缺失", "容量超額", "其他"],
                index=0
            )
        
        with col2:
            courses_involved = st.text_input(
                "涉及的課程",
                placeholder="例如：CS101, CS201, CS301"
            )
        
        conflict_desc = st.text_area(
            "詳細描述",
            placeholder="例如：這兩個課程在周一 9-11 點有時間衝突...",
            height=100
        )
        
        if st.button("💡 获取解決方案", use_container_width=True, type="primary"):
            with st.spinner("🔄 正在分析衝突..."):
                full_desc = f"""衝突類型: {conflict_type}
涉及課程: {courses_involved}
詳細信息: {conflict_desc}"""
                
                result = st.session_state.assistant.resolve_conflict(
                    st.session_state.student_id,
                    full_desc
                )
            
            st.markdown("#### 💡 解決方案")
            st.markdown(f"""
            <div class="success-box">
            {result['resolution']}
            </div>
            """, unsafe_allow_html=True)
    
    # ========================================================================
    # 標籤頁 5: 幫助指南
    # ========================================================================
    with tab5:
        st.markdown("### 📖 幫助指南")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🎯 系統功能
            
            **1. 智能問答**
            - 提出任何關於選課的問題
            - AI 會檢索相關課程並給出建議
            
            **2. 課程推薦**
            - 輸入興趣領域
            - AI 生成個性化推薦
            
            **3. 學習計劃**
            - 設定目標
            - AI 規劃完整的學習路徑
            
            **4. 衝突解決**
            - 描述遇到的問題
            - AI 提供解決方案
            """)
        
        with col2:
            st.markdown("""
            #### 💡 使用建議
            
            **提問技巧:**
            - ✅ 盡可能詳細地描述你的需求
            - ✅ 提及時間偏好、難度要求等
            - ✅ 告訴 AI 你的目標和興趣
            
            **系統特點:**
            - 🚀 完全本地運行，隱私安全
            - 💰 永久免費，零成本
            - ⚡ 即時響應（2-5 秒）
            - 🔄 支持多輪對話
            
            **需要幫助?**
            - 📚 查看文檔: README.md
            - 🔧 設置問題: OLLAMA_SETUP.md
            """)
        
        st.divider()
        
        # 統計信息
        st.markdown("#### 📊 會話統計")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("問題數量", len([h for h in st.session_state.chat_history if h['type'] == 'question']))
        with col2:
            st.metric("學生 ID", st.session_state.student_id)
        with col3:
            st.metric("會話時間", datetime.now().strftime("%H:%M"))
        with col4:
            st.metric("系統狀態", "✅ 正常")

# ============================================================================
# 頁腳
# ============================================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    #### 🚀 技術棧
    - **後端**: Python + Flask
    - **LLM**: Ollama + Mistral
    - **數據庫**: SQLite
    - **前端**: Streamlit
    """)

with col2:
    st.markdown("""
    #### 📚 相關資源
    - [Ollama 官網](https://ollama.ai)
    - [CourseHub 文檔](./README.md)
    - [Ollama 設置](./OLLAMA_SETUP.md)
    """)

with col3:
    st.markdown("""
    #### 📞 信息
    - **版本**: 1.0
    - **狀態**: 生產就緒
    - **成本**: 完全免費 ✅
    """)

st.markdown("""
<hr>
<p style="text-align: center; color: gray; font-size: 12px;">
🎓 CourseHub AI Assistant | 
Powered by Ollama & Mistral | 
100% Open Source & Free
</p>
""", unsafe_allow_html=True)
