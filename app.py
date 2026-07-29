with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""
            
            # 强化提示词：教育家长 + 功利性
            sys_prompt = f"""你是一个顶级的美国体育升学顾问。
            当前孩子{age}岁，家长的目标是{goal}。
            家长的认知较浅，你需要‘教育’他们体育对名校申请的‘入场券’作用。
            请用专业、直接、功利性的语气回答。
            注意：回复结束时必须带有 [建议问题] 标签并列出3个追问。"""

            try:
                # 构造消息列表，确保不包含空内容
                current_messages = [{"role": "system", "content": sys_prompt}]
                for m in st.session_state.messages:
                    if m["content"] and m["content"].strip(): # 过滤空消息
                        current_messages.append({"role": m["role"], "content": m["content"]})

                # 使用更稳定的模型 ID: llama-3.1-8b-instant
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=current_messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                
                ans = response.choices[0].message.content
                if ans:
                    full_response = ans
                    response_container.markdown(clean_response(full_response))
                    st.session_state.suggestions = extract_suggestions(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"抱歉，AI 顾问开小差了，错误原因: {str(e)}")
                # 如果 8b 报错，可以尝试在这里切换回 70b
