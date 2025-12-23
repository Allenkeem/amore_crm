import os
import streamlit as st
import requests
import json

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")

# -------------------------------------------------------------------------
# Page Config & Custom CSS
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Message Builder", 
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "chat_history" not in st.session_state:
    # History format: [{"prompt": str, "response_data": dict}, ...]
    st.session_state.chat_history = [] 

# Custom CSS for "Modal" Layout
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    /* Global Reset */
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
        color: #031B57; /* Deep Navy Text */
    }

    /* Background: Dimmed overlay effect */
    .stApp {
        background-color: #F5F9FF; /* Very Light Blue Background */
    }

    /* Main Container acting as the "Modal" */
    .block-container {
        background-color: #FFFFFF;
        max-width: 1000px;
        padding: 2rem 2rem 3rem 2rem;
        margin-top: 3rem;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(3, 27, 87, 0.08); /* Navy shadow */
    }
    
    /* Header Styling */
    .modal-header-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #031B57; /* Deep Navy */
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .modal-header-desc {
        font-size: 0.95rem;
        color: #6C6DD2; /* Medium Purple/Blue */
        margin-top: 4px;
        margin-bottom: 2rem;
    }
    
    /* Left Sidebar Styling */
    .sidebar-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #031B57;
        margin-bottom: 0.3rem;
        margin-top: 1rem;
    }
    
    /* Right Main Content Styling */
    .main-query-title {
        font-size: 1.6rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        color: #031B57;
    }
    
    /* --- Unified Capsule Chat UI --- */
    
    /* 1. Make the Form itself the "Capsule" container */
    [data-testid="stForm"] {
        background-color: #F0F5FF; /* Unified Light Blue Background */
        border-radius: 40px; /* High curvature (Capsule) */
        padding: 5px 10px; /* Internal spacing */
        border: none;
        box-shadow: 0 4px 20px rgba(3, 27, 87, 0.05); /* Subtle lift */
    }

    /* 2. Make Input Transparent so it blends in */
    /* Target the Baseweb Input Container */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background-color: transparent !important; /* Transparent to show Form bg */
        border: none !important;
        border-radius: 0px !important;
        padding: 0px 10px !important;
        height: 48px !important;
        min-height: 48px !important;
        align-items: center !important; 
        box-sizing: border-box !important;
        box-shadow: none !important;
    }
    
    /* Target internal wrappers */
    div[data-testid="stTextInput"] div[data-baseweb="base-input"], 
    div[data-testid="stTextInput"] div[data-baseweb="input"] > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Target the actual input element inside */
    div[data-testid="stTextInput"] div[data-baseweb="input"] input {
        background-color: transparent !important;
        border: none !important;
        color: #031B57 !important;
        height: 100% !important;
        padding: 0 !important;
        font-size: 1rem !important;
        box-shadow: none !important;
    }
    
    /* Placeholder Styling */
    div[data-testid="stTextInput"] div[data-baseweb="input"] input::placeholder {
        color: #6C6DD2 !important; 
        opacity: 1 !important; 
        -webkit-text-fill-color: #6C6DD2 !important;
    }

    /* Focus state - No harsh border, maybe subtle highlight on text? */
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Hide the default helper decoration */
    div[data-testid="stTextInput"] > div > div {
        border-radius: 0px; 
    }

    /* 3. Button Styling (Right side of capsule) */
    /* Action Button (Bottom Right) */
    .action-btn-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 1.5rem;
    }
    
    /* Target specifically the Form Submit Button */
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #2848FC !important; /* Key Color */
        color: white !important;
        border-radius: 50% !important; /* Perfect Circle */
        width: 45px !important; /* Slightly smaller to fit nicely */
        height: 45px !important;
        padding: 0 !important;
        font-size: 1.2rem !important;
        font-weight: 600;
        border: none !important;
        box-shadow: none !important; /* Clean flat integration */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
        margin-top: 2px; /* Slight alignment fix */
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #031B57 !important; 
        color: white !important;
        border: none !important;
    }

    /* Target generic buttons (Example buttons) to look like Chips */
    div[data-testid="stButton"] button {
        background-color: #FFFFFF !important;
        border: 1px solid transparent !important; /* Force override */
        border-radius: 20px !important;
        box-shadow: 0 2px 8px rgba(3, 27, 87, 0.05) !important;
        color: #526388 !important; /* Muted Blue-Gray Text */
        font-size: 0.9rem !important;
        padding: 0.4rem 1rem !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #F0F5FF !important; /* Light Hover */
        border-color: transparent !important;
        color: #2848FC !important; /* Active Blue Text */
        box-shadow: 0 4px 12px rgba(40, 72, 252, 0.1) !important;
    }
    div[data-testid="stButton"] button:active {
        background-color: #E0E7FF !important;
        color: #2848FC !important;
        border: none !important;
    }
    div[data-testid="stButton"] button:focus {
        border: none !important;
        outline: none !important;
        color: #2848FC !important;
    }
     
    /* Toggle Switch Customization */
    /* 1. Target by aria-checked on Label (Standard Baseweb) */
    label[data-baseweb="checkbox"][aria-checked="true"] > div:first-child {
        background-color: #2848FC !important;
    }
    label[data-baseweb="checkbox"][aria-checked="true"]:hover > div:first-child {
        background-color: #031B57 !important;
    }
    
    /* 2. Fallback: Target via Input:checked (if structure differs) */
    div[data-testid="stToggle"] input:checked + div {
        background-color: #2848FC !important;
    }
    div[data-testid="stToggle"] input:checked + div:hover {
        background-color: #031B57 !important;
    }

    /* Selectbox Customization - Focus Border */
    div[data-baseweb="select"] > div {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important; /* Remove default shadow if any */
    }
    /* When focused (Baseweb often uses a specific class or state, but :focus-within on the container works) */
    div[data-baseweb="select"]:focus-within > div {
        border: 1px solid #2848FC !important; /* Blue Border on Focus */
        box-shadow: 0 0 0 1px #2848FC !important; /* Blue Ring */
        background-color: #FFFFFF !important; /* Add white bg on focus for readability? Or keep transparent? User said "same as library" which usually means transparent static. Let's make it white on focus so it pops. */
    }
    /* Hover state */
    div[data-baseweb="select"]:hover > div {
        background-color: rgba(255, 255, 255, 0.5) !important; /* Slight hover effect */
    }

    /* Left Sidebar Column Styling */
    /* Target via :has() - supporting multiple potential testid names */
    [data-testid="stColumn"]:has(#sidebar-marker),
    [data-testid="column"]:has(#sidebar-marker) {
        background-color: #F8FBFF; /* Slightly darker/muted blue */
        border-radius: 20px;
        padding: 20px;
        border: none;
    }

    /* Library Expander Customization */
    div[data-testid="stExpander"] details {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] > details > summary {
        background-color: transparent !important;
        border: none !important;
    }

    /* Result Box */
    .result-box {
        background-color: #DCE6FD; /* Very Light Blue */
        border: 1px solid #CBD2FA;
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 2rem;
    }

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------------
# UI Layout
# -------------------------------------------------------------------------

# Header Row
# Full width header
st.markdown("""
    <div class="modal-header-title">
        <span style="color:#2848FC;">✨</span> AI 메시지 빌더
    </div>
    <div class="modal-header-desc">
        채널별로 원하는 스타일의 메시지를 쉽고 빠르게 생성해드려요.
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# Body Columns
col_left, col_right = st.columns([3, 7], gap="large")

# -------------------------------------------------------------------------
# Left Sidebar (Settings)
# -------------------------------------------------------------------------
with col_left:
    # Marker for CSS targeting
    st.markdown('<div id="sidebar-marker"></div>', unsafe_allow_html=True)
    
    # 1. Library Accordion
    with st.expander("📚 라이브러리", expanded=False):
        st.write("저장된 템플릿이 없습니다.")

    st.markdown('<div class="sidebar-label">발송 채널</div>', unsafe_allow_html=True)
    channel = st.selectbox(
        "발송 채널",
        ["앱푸시", "알림톡", "LMS", "마케팅 PUSH"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown('<div class="sidebar-label">메시지 톤</div>', unsafe_allow_html=True)
    tone = st.selectbox(
        "메시지 톤",
        ["기본", "친근한", "정중한", "위트있는", "감성적인"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Toggles
    use_past_tone = st.toggle("과거 메시지 톤 반영", value=False, help="이전 발송 이력을 분석하여 유사한 톤을 적용합니다.")
    use_personalization = st.toggle("메시지 개인화", value=False, help="고객의 이름이나 구매 이력을 포함합니다.")

# -------------------------------------------------------------------------
# Right Main Content (Input & Generate)
# -------------------------------------------------------------------------
with col_right:
    
    # Title (Only show if history is empty for cleaner look, or keep it?)
    # Let's keep it but maybe smaller if history exists? 
    # For now, keep as is.
    st.markdown("""
        <div style="text-align:center; color:#2848FC; font-size:2rem; margin-bottom:10px;">✍️</div>
        <div class="main-query-title">어떤 메시지를 작성하고 싶으신가요?</div>
    """, unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # 1. Render History Loop
    # -------------------------------------------------------------------------
    for chat_item in st.session_state.chat_history:
        prompt = chat_item["prompt"]
        data = chat_item.get("response_data")
        
        # A. User Message
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin-bottom:1rem;">
            <div style="background-color:#DCE6FD; color:#031B57; padding:10px 16px; border-radius:18px 18px 2px 18px; max-width:80%; font-size:0.95rem;">
                {prompt}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # B. AI Response (Analysis Cards)
        if data:
            final_msg = data.get("final_message", "Error")
            candidates = data.get("candidates", {})
            
            # Extract Info
            products = candidates.get("products", [])
            top_product = products[0] if products else {}
            top_persona = (candidates.get("personas") or ["미지정"])[0]
            top_purpose = (candidates.get("purposes") or ["-"])[0]
            detected_brand = candidates.get("detected_brand", "Unknown")
            brand_tone = candidates.get("brand_tone", "Default")
            
            # Message Box (Chat Bubble Style)
            st.markdown(f"""
                <div style="display:flex; justify-content:flex-start; margin-bottom:1.5rem;">
                    <div style="background-color:#F5F9FF; padding:20px; border-radius:4px 24px 24px 24px; max-width:85%; box-shadow: 0 2px 12px rgba(3, 27, 87, 0.04);">
                        <div style="font-weight:700; color:#2848FC; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                            <span>🤖</span> 생성된 결과
                        </div>
                        <div style="white-space: pre-wrap; line-height:1.6; color:#031B57;">{final_msg}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Cards - Align width with Message Bubble (85%)
            layout_c, _ = st.columns([0.85, 0.15])
            with layout_c:
                # 1. Persona Card
                st.markdown(f"""
                <div style="background:#fff; border:none; border-radius:16px; padding:12px 20px; margin-bottom:8px; box-shadow: 0 2px 8px rgba(3, 27, 87, 0.05);">
                    <div style="color:#000000; font-size:0.75rem; margin-bottom:2px; opacity:0.6;">🎯 타겟 페르소나</div>
                    <div style="font-weight:700; color:#000000; font-size:0.95rem; line-height:1.2;">{top_persona}</div>
                    <div style="font-size:0.8rem; color:#000000; margin-top:2px;">{top_purpose}</div>
                </div>""", unsafe_allow_html=True)

                # 2. Product Card
                st.markdown(f"""
                <div style="background:#fff; border:none; border-radius:16px; padding:12px 20px; margin-bottom:8px; box-shadow: 0 2px 8px rgba(3, 27, 87, 0.05);">
                    <div style="color:#000000; font-size:0.75rem; margin-bottom:2px; opacity:0.6;">📦 추천 상품</div>
                    <div style="font-weight:700; color:#000000; font-size:0.95rem; line-height:1.2;">{top_product.get('name', 'None')}</div>
                    <div style="font-size:0.8rem; color:#000000; margin-top:2px;">{top_product.get('brand','')}</div>
                </div>""", unsafe_allow_html=True)
                
                # 3. Tone Card
                st.markdown(f"""
                <div style="background:#fff; border:none; border-radius:16px; padding:12px 20px; margin-bottom:8px; box-shadow: 0 2px 8px rgba(3, 27, 87, 0.05);">
                    <div style="color:#000000; font-size:0.75rem; margin-bottom:2px; opacity:0.6;">🎨 브랜드 톤</div>
                    <div style="font-weight:700; color:#000000; font-size:0.95rem; line-height:1.2;">{detected_brand}</div>
                    <div style="font-size:0.8rem; color:#000000;">{brand_tone}</div>
                </div>""", unsafe_allow_html=True)
                
            st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)


    # -------------------------------------------------------------------------
    # 2. Recommendation Chips (Placed ABOVE input)
    # -------------------------------------------------------------------------
    # Recommendation List
    # Recommendation List
    examples = [
        "👋 신규 회원가입을 환영하는 메시지를 작성해주세요.",
        "🎁 신규 고객을 위한 첫 구매 20% 할인 쿠폰 메시지",
        "💄 라네즈 크림스킨 추천 메시지"
    ]
    
    # Horizontal Layout (3 columns)
    rc1, rc2, rc3 = st.columns(3)
    
    # Helper for button click
    def click_example(ex_text):
        st.session_state.input_text = ex_text
        st.rerun()

    if rc1.button("👋 신규 가입 환영", help=examples[0], use_container_width=True):
        click_example(examples[0])
    if rc2.button("🎁 첫 구매 할인", help=examples[1], use_container_width=True):
        click_example(examples[1])
    if rc3.button("💄 라네즈 추천", help=examples[2], use_container_width=True):
        click_example(examples[2])



    # -------------------------------------------------------------------------
    # 3. Input Area (Fixed at bottom via Layout order)
    # -------------------------------------------------------------------------
    
    # Placeholder for spinner/loading state ABOVE the input
    loading_container = st.empty()

    # Chat Bar Layout
    with st.form(key="chat_form", clear_on_submit=True): # clear_on_submit=True for better chatUX
        c_input, c_btn = st.columns([9, 1], gap="small")
        with c_input:
            user_input = st.text_input(
                "Message",
                value=st.session_state.input_text,
                placeholder="메시지를 입력하세요...",
                label_visibility="collapsed"
            )
        with c_btn:
            submit_btn = st.form_submit_button("➤")
    
    # Handle Submit
    if submit_btn:
        st.session_state.input_text = user_input # Update state
        if not user_input:
            st.markdown("""
            <div style="background-color:#DCE6FD; color:#031B57; padding:10px; border-radius:8px; border:1px solid #2848FC; margin-bottom:10px; font-size:0.9rem;">
                ⚠️ 메시지 내용을 입력해주세요.
            </div>
            """, unsafe_allow_html=True)
        else:
            # 1. Show Custom "Thinking" Animation
            loading_html = """
            <style>
            @keyframes blink {
                0% { opacity: 0.2; transform: scale(1); }
                20% { opacity: 1; transform: scale(1.2); }
                100% { opacity: 0.2; transform: scale(1); }
            }
            .typing-indicator {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background-color: #F5F9FF; /* Same as AI bubble */
                padding: 12px 20px;
                border-radius: 4px 24px 24px 24px; /* Same rounded corner */
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                margin-bottom: 10px;
                width: fit-content;
            }
            .typing-dot {
                width: 8px;
                height: 8px;
                background-color: #2848FC; /* Brand Blue */
                border-radius: 50%;
                animation: blink 1.4s infinite both;
            }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            </style>
            
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            """
            
            with loading_container:
                st.markdown(loading_html, unsafe_allow_html=True)
                try:
                    full_prompt = f"[{channel}] {user_input}"
                    if tone != "기본":
                         full_prompt += f" (톤: {tone})"
                    
                    response = requests.post(BACKEND_URL, json={"message": full_prompt})
                    if response.status_code == 200:
                        data = response.json()
                        final_msg = data.get("final_message", "")
                        
                        # Streaming Simulation
                        stream_placeholder = st.empty()
                        # We need to render the bubble structure but update text
                        # Since the history loop is above, we can use a placeholder located there
                        # But wait, we act specifically *after* the history loop. 
                        # We need to find where the history loop ends. 
                        # To make this work cleanly, we should output the stream content *here*, 
                        # but "here" is inside the form logic which might be visually below the inputs if not careful.
                        # Actually, `loading_container` is ABOVE the input. We can reuse it or a new one!
                        # `loading_container` is where the spinner/animation was. 
                        # Let's use `loading_container` for streaming too!
                        
                        full_html_template = """
                        <div style="display:flex; justify-content:flex-start; margin-bottom:1.5rem;">
                            <div style="background-color:#F5F9FF; padding:20px; border-radius:4px 24px 24px 24px; max-width:85%; box-shadow: 0 2px 12px rgba(3, 27, 87, 0.04);">
                                <div style="font-weight:700; color:#2848FC; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                                    <span>🤖</span> 생성된 결과
                                </div>
                                <div style="white-space: pre-wrap; line-height:1.6; color:#031B57;">{text}</div>
                            </div>
                        </div>
                        """
                        
                        import time
                        step_size = 3 # chars per step
                        for i in range(0, len(final_msg) + 1, step_size):
                            current_text = final_msg[:i]
                            # Update the container
                            with loading_container:
                                st.markdown(full_html_template.format(text=current_text), unsafe_allow_html=True)
                            time.sleep(0.01) # fast typing
                            
                        # Append to History
                        st.session_state.chat_history.append({
                            "prompt": user_input,
                            "response_data": data
                        })
                        # Clear input state for next turn
                        st.session_state.input_text = ""
                        st.rerun()
                    else:
                        st.error(f"Error {response.status_code}")
                except Exception as e:
                    st.error(f"Connection Failed: {e}")