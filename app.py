import streamlit as st
from groq import Groq
import re

# 1. 页面基本配置 (必须是 Streamlit 命令的第一行)
st.set_page_config(page_title="小将名校之路", page_icon="🎓")

# 2. 初始化 Groq 客户端
client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.sidebar.warning("⚠️ 请在 Secrets 中配置 GROQ_API_KEY")

# 3. 辅助函数：处理建议问题和清洗文本
def extract_suggestions(text):
    """从AI回复中提取[建议问题]标签后的内容"""
    pattern = r"\[建议问题\](.*)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        raw_sug = match.group(1).strip()
        sugs = [re.sub(r"^\d+[\.\s、]+", "", s).strip() for s in raw_sug.split('\n') if s.strip()]
        return sugs[:3]
    return []

def clean_response(text):
    """去掉AI回复中的标签"""
    return re.sub(r"\[建议问题\].*", "", text, flags=re.DOTALL).strip()

# 4. 初始化 Session State (存储对话状态)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ["体育真的能帮孩子进藤校吗？", "哪种运动对小升初最加分？", "走体育路径一年要花多少钱？"]

# 5. 侧边栏：家长画像
with st.sidebar:
    st.title("🎯 升学目标档案")
    age = st.slider("孩子年龄", 5, 12, 8)
    goal = st.selectbox("核心诉求", ["想进藤校/名校", "想拿奖学金", "还没想好，先了解"])
    if st.button("🔄 开启新咨询"):
        st.session_state.messages = []
        st.session_state.suggestions = ["体育真的能帮孩子进藤校吗？", "哪种运动对小升初最加分？", "走体育路径一年要花多少钱？"]
        st.rerun()

# 6. 主界面渲染
st.title("🎓 美国名校体育升学规划")
st.info("专注小学阶段体育规划，把体育特长转化为名校‘入场券’。")

# 展示历史对话
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(clean_response(msg["content"]))

# 7. 引导式按钮 (解决家长问不出问题)
st.write("---")
if st.session_state.suggestions:
    st.caption("🔍 您可能想深度了解：")
    # 使用 columns 让按钮横向排列
    cols = st.columns(len(st.session_state.suggestions))
    for i, q in enumerate(st.session_state.suggestions):
        if cols[i].button(q, key=f"sug_btn_{i}"):
            st.session_state.user_input = q

# 8. 对话核心逻辑
# 处理两种输入：手动输入或点击建议按钮
prompt = st.chat_input("在此输入您的疑问...")
user_query = prompt if prompt else st.session_state.get("user_input")

if user_query:
    # 清理掉临时的按钮输入状态
    if "user_input" in st.session_state:
        del st.session_state["user_input"]

    if not client:
        st.error("未检测到 API Key，请在侧边栏查看说明。")
    else:
        # 将用户问题存入历史
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        # AI 回答逻辑
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # 教育性 + 功利性 System Prompt
            sys_prompt = f"""你是一个顶级的美国大学体育升学顾问。
            当前孩子{age}岁，家长的目标是{goal}。
            家长的认知可能较浅，你需要‘教育’他们体育对名校申请的‘入场券’(Hook)作用。
            请用专业、直接、功利性的语气回答，多谈投入产出比和录取优势。
            注意：每次回复最后必须包含 [建议问题] 标签，并列出3个相关的追问。"""

            try:
                # 过滤空消息并调用 API
                valid_history = [{"role": "system", "content": sys_prompt}]
                for m in st.session_state.messages:
                    if m["content"].strip():
                        valid_history.append({"role": m["role"], "content": m["content"]})

                # 使用目前最稳定的免费模型
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=valid_history,
                    temperature=0.7
                )
                
                full_res = response.choices[0].message.content
                response_placeholder.markdown(clean_response(full_res))
                
                # 更新建议问题并刷新
                st.session_state.suggestions = extract_suggestions(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()

            except Exception as e:
                st.error(f"咨询顾问暂时掉线了: {str(e)}")
