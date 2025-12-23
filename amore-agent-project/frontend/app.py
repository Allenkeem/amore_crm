import streamlit as st
import requests
import json

# Configuration
BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Amore AI Agent (Chat)", layout="wide")

st.title("🤖 AmorePacific AI Agent (Chat Mode)")
st.markdown("자연어로 요청하면 제품 검색부터 메시지 생성까지 한 번에 처리합니다.")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

# Layout: Left for Chat, Right for Dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("대화창")
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("예: 실용적인 30대 맘한테 라네즈 크림스킨 재구매하라고 문자 보내줘"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call Backend
        with st.spinner("AI가 분석 및 메시지 생성 중입니다..."):
            try:
                response = requests.post(BACKEND_URL, json={"message": prompt})
                
                if response.status_code == 200:
                    data = response.json()
                    final_msg = data.get("final_message", "응답 없음")
                    
                    # Construct display message (similar to previous Gradio logic or just the message)
                    # The user's prompt implied they liked the "Analysis Result" block in the chat.
                    # Let's reproduce a simplified version or just show the final message + dashboard.
                    # For a clean chat, I'll show the final generated message here.
                    
                    bot_response = final_msg
                    
                    # Display assistant response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(bot_response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    
                    # Save analysis for dashboard
                    st.session_state.last_analysis = data
                    
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

with col2:
    st.subheader("📊 분석 대시보드")
    
    if st.session_state.last_analysis:
        data = st.session_state.last_analysis
        candidates = data.get("candidates", {})
        parsed = data.get("parsed", {})
        
        # Extract meaningful info
        products = candidates.get("products", [])
        top_product = products[0].get("name", "None") if products else "없음"
        
        personas = candidates.get("personas", [])
        top_persona = personas[0] if personas else "없음"
        
        purposes = candidates.get("purposes", [])
        top_purpose = purposes[0] if purposes else "없음"
        
        extracted_persona = parsed.get("extracted", {}).get("persona", "None")
        detected_brand = candidates.get("detected_brand", "Unknown")
        brand_tone = candidates.get("brand_tone", "Unknown")
        
        # Display Cards
        st.info(f"**📦 제품**: {top_product}")
        st.success(f"**🎯 페르소나**: {top_persona}")
        st.warning(f"**🎨 브랜드/톤**: {detected_brand} / {brand_tone}")
        st.error(f"**🔄 목적**: {top_purpose}")
        
        with st.expander("🔍 상세 분석 데이터 (JSON)"):
            st.json(data)
    else:
        st.info("대화를 시작하면 분석 결과가 여기에 표시됩니다.")