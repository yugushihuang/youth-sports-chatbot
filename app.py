import streamlit as st
from groq import Groq
import re

# 1. 页面配置
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
    st.session_state.suggestions = [
        "为什么硅谷娃卷钢琴不如卷击剑/壁球？",
        "坐标西海岸，哪些项目是藤校的‘特权入场券’？",
        "GPA 4.0 够吗？体育能帮娃降分进斯坦福吗？"
    ]

# --- 5. 手机端优化：主页置顶画像设置 ---
st.title("🤺 弯道超车：西海岸娃的体育名校入场券")

# 使用 expander 让用户在手机上也能一眼看到并修改
with st.expander("📊 第一步：配置您的升学黑客档案（手机端必填）", expanded=len(st.session_state.messages) == 0):
    col1, col2 = st.columns(2)
    with col1:
        location = st.selectbox("坐标", ["湾区 (Bay Area)", "西雅图 (Seattle)", "洛杉矶 (LA)", "其他"])
        child_age = st.slider("孩子年龄", 5, 12, 8)
    with col2:
        budget = st.selectbox("年度体育预算", ["1-3万美金", "3-5万美金", "不设上限 (All-in)"])
        target = st.selectbox("核心目标", ["常青藤/斯坦福 (D1)", "学术强校 (D3)", "还没想好"])
    
    if st.button("🚀 生成/更新我的专属规划", use_container_width=True):
        st.session_state.messages = [] # 重置对话
        st.session_state.suggestions = ["为什么硅谷娃卷钢琴不如卷击剑？", "哪些项目藤校录取率最高？", "体育能帮娃降分进名校吗？"]
        st.success("配置成功！请在下方开始咨询。")

st.markdown(f"**当前定位：** {location} | {child_age}岁 | 预算 {budget}")
st.write("---")

# 6. 展示历史记录
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(clean_response(msg["content"]))

# 7. 引导式追问按钮（手机端友好，点击即可）
if st.session_state.suggestions:
    st.caption("🔥 硅谷家长圈都在问：")
    # 手机端建议竖着排或者小块排，Streamlit 自动处理 columns 的堆叠
    for i, q in enumerate(st.session_state.suggestions):
        if st.button(q, key=f"sug_btn_{i}", use_container_width=True):
            st.session_state.user_input = q

# 8. 对话核心逻辑
prompt = st.chat_input("输入疑问，例如：娃现在练游泳还有前途吗？")
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
            
            # System Prompt 注入
            sys_prompt = f"""你是一个专门服务西海岸（硅谷、西雅图等）高净值华人家长的顶级体育升学顾问。
            孩子{child_age}岁，坐标{location}，年度预算{budget}，目标{target}。
            
            你的核心任务：
            1. 教育家长：解释什么是 NCAA Recruiting 里的 'Hook'。解释为什么 10 年级才开始体育规划在竞争激烈的西海岸就是‘慢性自杀’。
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
