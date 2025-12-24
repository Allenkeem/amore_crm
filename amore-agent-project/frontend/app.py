import os
import streamlit as st
import requests
import json
import base64

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")

# -------------------------------------------------------------------------
# Page Config & Custom CSS
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="CRM 메시지 자동 제작 에이전트", 
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
    /* Right Align Container */
    div[data-testid="stButton"] {
        display: flex;
        justify-content: flex-end;
    }

    div[data-testid="stButton"] button {
        background-color: #FFFFFF !important;
        border: 1px solid transparent !important; /* Force override */
        border-radius: 20px !important;
        box-shadow: 0 2px 8px rgba(3, 27, 87, 0.05) !important;
        color: #526388 !important; /* Muted Blue-Gray Text */
        font-size: 0.85rem !important; /* Readable Size */
        padding: 0.25rem 2rem !important; /* Thinner height, Wider width */
        transition: all 0.2s !important;
        width: auto !important; /* Auto Width */
        white-space: normal !important; /* Allow wrapping if needed */
        height: auto !important; /* Allow growing */
        min-height: 0px !important; /* Override Streamlit default */
        line-height: 1.2 !important; /* tighter text */
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

    /* Toast Customization */
    div[data-testid="stToast"] {
        width: auto !important;
        max-width: 50% !important;
        min-width: 400px !important;
        padding: 16px !important;
    }
    div[data-testid="stToast"] > div {
        white-space: nowrap !important;
    }

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------------
# UI Layout
# -------------------------------------------------------------------------

# Header Row
# Full width header
def get_image_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_image_base64("data/amoremall_og_img.png")

st.markdown(f"""
    <div style="background-color:#2e3982; padding:2rem 2rem 1.5rem 2rem; border-radius:16px 16px 0 0; margin-top:-2rem; margin-left:-2rem; margin-right:-2rem; margin-bottom:0; text-align:center;">
        <img src="data:image/png;base64,{img_base64}" style="max-width:100%; height:auto; margin-bottom: 1rem;">
        <div class="modal-header-title" style="color:#FFFFFF; justify-content:center;">
            <span style="color:#FFF;">✨</span> CRM 메시지 자동 제작 에이전트
        </div>
        <div class="modal-header-desc" style="color:#E0E7FF; margin-top:4px; margin-bottom:0;">
            고객 페르소나를 바탕으로 각 개인에게 맞는 아모레몰 상품을 추천하는 마케팅 메시지를 만들어드려요
        </div>
    </div>
    <hr style="margin-top: 0; margin-bottom: 1rem; border: 0; border-top: 1px solid #E1E8F5;">
""", unsafe_allow_html=True)

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
            # Only show cards if we have valid analysis data (not None)
            if detected_brand and brand_tone:
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

                    # 4. Target Audience (New)
                    target_audience = data.get("target_audience")
                    if target_audience:
                        seg_name = target_audience.get("segment_name", "Target")
                        count = target_audience.get("count", 0)
                        desc = target_audience.get("description", "")
                        
                        # Card: Title, Description, Count
                        st.markdown(f"""
                        <div style="background:#F5F9FF; border:none; border-radius:16px; padding:16px 20px; margin-top:12px; margin-bottom:8px; box-shadow: 0 2px 12px rgba(3, 27, 87, 0.04);">
                            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                                <span style="font-size:1.2rem;">👥</span>
                                <div style="font-weight:700; color:#2848FC; font-size:1rem;">적합한 고객 세그먼트</div>
                            </div>
                            <div style="font-weight:600; color:#2D3748; margin-bottom:4px;">{desc}</div>
                            <div style="font-size:0.9rem; color:#4A5568;">총 <span style="color:#2B6CB0; font-weight:700;">{count}명</span>의 고객이 있습니다.</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Customer List (Expander) - Outside
                        customer_ids = target_audience.get("sample_ids", [])
                        if customer_ids:
                            with st.expander(f"📋 대상 고객 목록 ({len(customer_ids)}명)", expanded=False):
                                st.dataframe(
                                    {"Customer ID": customer_ids},
                                    use_container_width=True,
                                    height=150,
                                    hide_index=True
                                )

                        # Button - Outside
                        if st.button("CRM 메시지 전송", key=f"btn_send_{hash(str(chat_item))}", use_container_width=True):
                            st.toast(f"{count}명의 고객에게 메시지 발송을 예약했습니다!", icon="🚀")
                
            st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)


    # -------------------------------------------------------------------------
    # 2. Recommendation Chips (Placed ABOVE input)
    # -------------------------------------------------------------------------
    # Dynamic Proposals from Session State (or Defaults)
    current_suggestions = st.session_state.get("latest_suggestions", [
        "👋 신규 회원가입을 환영하는 메시지를 작성해주세요.",
        "🎁 신규 고객을 위한 첫 구매 20% 할인 쿠폰 메시지",
        "💄 라네즈 크림스킨 추천 메시지"
    ])
    
    # Vertical Stack Layout
    # Use full width for each button to accommodate long text
    
    # Helper for button click
    def click_example(ex_text):
        st.session_state.input_text = ex_text
        st.rerun()

    s1 = current_suggestions[0] if len(current_suggestions) > 0 else "추천 1"
    s2 = current_suggestions[1] if len(current_suggestions) > 1 else "추천 2"
    s3 = current_suggestions[2] if len(current_suggestions) > 2 else "추천 3"
    
    if st.button(s1, key="sbtn1", use_container_width=False):
        click_example(s1)
    
    if st.button(s2, key="sbtn2", use_container_width=False):
        click_example(s2)
        
    if st.button(s3, key="sbtn3", use_container_width=False):
        click_example(s3)



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
            # 1. Show Custom "Thinking" Animation with Dynamic Status
            # 1. Show Custom "Thinking" Animation with Dynamic Status
            # Dynamic content is now handled by the stream loop below.
            status_html_template = """
            <div style="display:flex; align-items:center; gap:12px; background-color:#F5F9FF; padding:16px 24px; border-radius:12px; border:1px solid #E1E8F5; margin-bottom:24px; width:fit-content;">
                <div style="width:20px; height:20px; border:3px solid #E1E8F5; border-top:3px solid #2848FC; border-radius:50%; animation:spin 1s linear infinite;"></div>
                <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
                <div style="font-size:0.95rem; color:#526388; font-weight:500;">요청을 준비 중입니다...</div>
            </div>
            """
            
            # 1. Reuse the container above the input
            status_container = loading_container
            
            # Helper to render the Status Bubble (Minimalist)
            def render_status_bubble(current_status):
                html = f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding-left: 4px;">
                    <div style="width:16px; height:16px; border:2px solid #E1E8F5; border-top:2px solid #2848FC; border-radius:50%; animation:spin 1s linear infinite;"></div>
                    <style>@keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
                    <span style="font-size:0.9rem; color:#526388; font-weight:500;">{current_status}</span>
                </div>
                """
                return html

            try:
                full_prompt = f"[{channel}] {user_input}"
                if tone != "기본":
                        full_prompt += f" (톤: {tone})"
                
                # Prepare Chat History (Last 2 Turns)
                chat_history = []
                if "chat_history" in st.session_state and len(st.session_state.chat_history) > 0:
                    # Get last 2 interactions
                    recent_turns = st.session_state.chat_history[-2:]
                    for item in recent_turns:
                        chat_history.append({"role": "user", "content": item["prompt"]})
                        if item.get("response_data"):
                            chat_history.append({"role": "assistant", "content": item["response_data"].get("final_message", "")})
                
                # Request with stream=True
                payload = {"message": full_prompt, "history": chat_history}
                with requests.post(BACKEND_URL, json=payload, stream=True) as response:
                    if response.status_code == 200:
                        
                        # Temp storage for final history
                        collected_data = {
                            "candidates": {},
                            "final_message": "",
                            "parsed": {},
                            "audit_trail": []
                        }
                        
                        current_status_msg = "연결 중..."
                        status_container.markdown(render_status_bubble(current_status_msg), unsafe_allow_html=True)
                        
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                if decoded_line.startswith("data: "):
                                    json_str = decoded_line[6:] # remove "data: "
                                    try:
                                        event = json.loads(json_str)
                                        evt_type = event.get("type")
                                        
                                        if evt_type == "status":
                                            # Update Status Text
                                            current_status_msg = event.get("msg", "...")
                                            status_container.markdown(render_status_bubble(current_status_msg), unsafe_allow_html=True)
                                            
                                        elif evt_type == "data":
                                            key = event.get("key")
                                            val = event.get("value")
                                            
                                            if key == "candidates":
                                                collected_data["candidates"] = val
                                                # Product logging removed
                                                
                                            elif key == "final_message":
                                                collected_data["final_message"] = val
                                                # We don't render final message here to avoid visual glitch.
                                                # It will be rendered when the history loop updates.
                                                
                                            elif key == "audit_trail":
                                                collected_data["audit_trail"] = val
                                            elif key == "parsed":
                                                collected_data["parsed"] = val
                                                
                                            elif key == "suggestions":
                                                collected_data["suggestions"] = val
                                            
                                            elif key == "target_audience":
                                                collected_data["target_audience"] = val
                                        
                                        elif evt_type == "error":
                                            st.error(f"Server Error: {event.get('msg')}")
                                            
                                    except json.JSONDecodeError:
                                        continue
                        
                        # Stream Finished
                        status_container.empty() # Remove status bar
                        
                        # Update Suggestions for Next Turn
                        if "suggestions" in collected_data:
                            st.session_state.latest_suggestions = collected_data["suggestions"]
                        
                        # Add to History
                        st.session_state.chat_history.append({
                            "prompt": user_input,
                            "response_data": collected_data
                        })
                        st.session_state.input_text = ""
                        st.rerun()
                        
                    else:
                        st.error(f"Error {response.status_code}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")