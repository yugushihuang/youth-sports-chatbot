import streamlit as st
from groq import Groq # 换成免费的 Groq
import re

# 页面配置
st.set_page_config(page_title="小将名校之路", page_icon="🎓")

# --- 1. 初始化免费的 Groq 客户端 ---
# 你稍后在 Streamlit Secrets 里填入 GROQ_API_KEY 即可
client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.sidebar.warning("请在 Secrets 中配置 GROQ_API_KEY (免费获取: console.groq.com)")

# --- 2. 核心逻辑：提取建议问题 ---
def extract_suggestions(text):
    pattern = r"\[建议问题\](.*)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        raw_sug = match.group(1).strip()
        sugs = [re.sub(r"^\d+[\.\s、]+", "", s).strip() for s in raw_sug.split('\n') if s.strip()]
        return sugs[:3]
    return []

def clean_response(text):
    return re.sub(r"\[建议问题\].*", "", text, flags=re.DOTALL).strip()

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("🎯 升学目标")
    age = st.slider("孩子年龄", 5, 12, 8)
    goal = st.selectbox("核心诉求", ["想进藤校/名校", "想拿奖学金", "还没想好，先了解"])
    if st.button("开启新咨询"):
        st.session_state.messages = []
        st.session_state.suggestions = ["体育真的能帮孩子进藤校吗？", "哪种运动对小升初最加分？", "走体育路径一年要花多少钱？"]
        st.rerun()

# --- 4. 界面渲染 ---
st.title("🎓 美国名校体育升学规划")
st.caption("针对小学生家长的‘功利性’体育启蒙指南")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["体育真的能帮孩子进藤校吗？", "哪种运动对小升初最加分？", "走体育路径一年要花多少钱？"]

# 渲染对话
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(clean_response(msg["content"]))

# 建议问题按钮
st.write("---")
if st.session_state.suggestions:
    st.caption("🔍 点击深度追问（教育家长专用）：")
    cols = st.columns(len(st.session_state.suggestions))
    for i, q in enumerate(st.session_state.suggestions):
        if cols[i].button(q, key=f"btn_{i}"):
            st.session_state.user_input = q

# --- 5. 对话逻辑 ---
input_text = st.chat_input("输入疑问...") 
if input_text or st.session_state.get("user_input"):
    query = input_text if input_text else st.session_state.user_input
    if "user_input" in st.session_state: del st.session_state.user_input

    if not client:
        st.error("请先在 Secrets 中填入免费的 GROQ_API_KEY")
    else:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            # 强化“功利性”和“教育性”的提示词
            sys_prompt = f"""你是一个顶级的美国体育升学顾问。你的目标是教育那些不懂体育升学的功利性家长。
            孩子{age}岁，目标是{goal}。
            请用专业、揭秘、略带功利性的语气回答。
            每一段回复必须以 [建议问题] 结尾，并列出3个让家长感到‘必须立刻追问’的问题。"""
            
            # 使用免费的 llama3-70b 模型
            response = client.chat.completions.create(
                model="llama3-70b-8192", 
                messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages
            )
            ans = response.choices[0].message.content
            st.markdown(clean_response(ans))
            
            st.session_state.suggestions = extract_suggestions(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()
