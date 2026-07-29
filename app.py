import streamlit as st
from groq import Groq
import re

# 1. 页面配置：更有冲击力的标题
st.set_page_config(page_title="西海岸体育升学黑客", page_icon="🤺")

# 2. 初始化 Groq 客户端
client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.sidebar.warning("⚠️ 请在 Secrets 中配置 GROQ_API_KEY")

# 3. 辅助函数
def extract_suggestions(text):
    pattern = r"\[深挖问题\](.*)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        raw_sug = match.group(1).strip()
        sugs = [re.sub(r"^\d+[\.\s、]+", "", s).strip() for s in raw_sug.split('\n') if s.strip()]
        return sugs[:3]
    return []

def clean_response(text):
    return re.sub(r"\[深挖问题\].*", "", text, flags=re.DOTALL).strip()

# 4. 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestions" not in st.session_state:
    # 针对西海岸家长的第一组建议问题（极具吸引力）
    st.session_state.suggestions = [
        "为什么硅谷娃卷钢琴不如卷击剑/壁球？",
        "坐标西海岸，哪些运动是藤校的‘特权入场券’？",
        "GPA 4.0 够吗？体育能帮娃降分进斯坦福吗？"
    ]

# 5. 侧边栏：精准画像
with st.sidebar:
    st.title("🛡️ 升学黑客档案")
    location = st.selectbox("坐标", ["湾区 (Bay Area)", "西雅图 (Seattle)", "洛杉矶 (LA)", "其他"])
    child_age = st.slider("孩子年龄", 5, 12, 8)
    financial_budget = st.selectbox("年度体育预算", ["1-3万美金", "3-5万美金", "不设上限 (All-in)"])
    
    if st.button("🔄 重置升学规划"):
        st.session_state.messages = []
        st.session_state.suggestions = ["为什么硅谷娃卷钢琴不如卷击剑？", "哪些项目藤校录取率最高？", "体育能帮娃降分进名校吗？"]
        st.rerun()

# 6. 主界面：直接切入痛点
st.title("🤺 弯道超车：西海岸娃的体育名校入场券")
st.markdown(f"""
> **针对{location}华人家长的专属规划**  
> 在西海岸，GPA 满分只是起跑线。我们将带您拆解如何利用 **NCAA Recruiting** 规则，把体育从“课外活动”变成**名校录取时的“核武器”**。
""")

# 展示历史
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(clean_response(msg["content"]))

# 7. 引导式按钮（解决家长不懂问的问题）
st.write("---")
if st.session_state.suggestions:
    st.caption("🔥 大家都想问：")
    cols = st.columns(len(st.session_state.suggestions))
    for i, q in enumerate(st.session_state.suggestions):
        if cols[i].button(q, key=f"sug_btn_{i}"):
            st.session_state.user_input = q

# 8. 对话核心逻辑
prompt = st.chat_input("输入您的升学困惑（如：娃还没定项，怎么选回报率最高？）")
user_query = prompt if prompt else st.session_state.get("user_input")

if user_query:
    if "user_input" in st.session_state:
        del st.session_state["user_input"]

    if not client:
        st.error("API Key 未配置。")
    else:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # 【核心核心】：System Prompt 决定了 AI 的深度
            sys_prompt = f"""你是一个专门服务西海岸（硅谷、西雅图等）高净值华人家长的顶级体育升学顾问。
            孩子{child_age}岁，坐标{location}，预算{financial_budget}。
            
            你的核心任务：
            1. 教育家长：解释什么是 NCAA Recruiting 里的 'Hook'。强调 10 年级才开始体育规划就太晚了。
            2. 功利分析：对比常见项目（游泳、钢琴、数学）与名校招募项目（击剑、壁球、高尔夫、赛艇）的录取率差异。
            3. 避坑指南：西海岸华人家庭最容易跟风练什么，结果却成了陪跑？
            4. 语气：睿智、深刻、功利、有揭秘感，像一个掌握内幕的藤校前招生官。
            
            每次回复必须以 [深挖问题] 标签结束，列出3个让家长感到扎心、不得不点的功利追问。"""

            try:
                valid_history = [{"role": "system", "content": sys_prompt}]
                for m in st.session_state.messages:
                    if m["content"].strip():
                        valid_history.append({"role": m["role"], "content": m["content"]})

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=valid_history,
                    temperature=0.8
                )
                
                full_res = response.choices[0].message.content
                response_placeholder.markdown(clean_response(full_res))
                
                st.session_state.suggestions = extract_suggestions(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()

            except Exception as e:
                st.error(f"顾问暂时休假: {str(e)}")
