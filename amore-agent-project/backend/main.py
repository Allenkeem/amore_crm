import gradio as gr
import sys
import os

# -------------------------------------------------------------------------
# Path Setup
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from services.crm_agent.orchestrator import get_orchestrator

# -------------------------------------------------------------------------
# Initialize
# -------------------------------------------------------------------------
print("Initializing Orchestrator...")
orch = get_orchestrator()

# -------------------------------------------------------------------------
# Logic Handler
# -------------------------------------------------------------------------
def chat_handler(user_message, history):
    if not user_message:
        return "", history, None
        
    # 1. Orchestrator Process
    results = orch.process_query(user_message)
    
    # 2. Format Response for Chatbot (Simple Text)
    # We will show the detailed candidates in the JSON output panel
    final_msg = results.get("final_message", "Error generation message.")
    
    # Construct a rich response text
    candidates = results.get("candidates", {})
    
    products = candidates.get("products", [])
    top_product = products[0].get("name", "None") if products else "없음"
    
    personas = candidates.get("personas", [])
    top_persona = personas[0] if personas else "없음"
    
    purposes = candidates.get("purposes", [])
    top_purpose = purposes[0] if purposes else "없음"
    
    # Parse additional details
    parsed = results.get("parsed", {})
    extracted_persona = parsed.get("extracted", {}).get("persona", "None")
    
    detected_brand = candidates.get("detected_brand", "Unknown")
    brand_tone = candidates.get("brand_tone", "Unknown")
    
    bot_response = f"""
**[분석 결과]**
📦 제품: {top_product}
🏷️ 브랜드: {detected_brand}
🔑 추출 키워드: {extracted_persona}
🎯 매칭 페르소나: {top_persona}
🎨 브랜드 톤: {brand_tone}
🔄 목적: {top_purpose}

**[생성된 메시지]**
{final_msg}
"""
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_response})
    
    return "", history, results

# -------------------------------------------------------------------------
# UI Layout (Chat Centric)
# -------------------------------------------------------------------------
custom_css = """
body { font-family: 'Pretendard', sans-serif !important; background-color: #f8f9fa; }
.header-area { text-align: center; margin-bottom: 1rem; }
.chatbot { height: 600px !important; overflow-y: auto; }
"""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="Amore AI Agent (Chat)") as demo:
    
    with gr.Column(elem_classes="header-area"):
        gr.Markdown("## 🤖 AmorePacific AI Agent (Chat Mode)")
        gr.Markdown("자연어로 요청하면 제품 검색부터 메시지 생성까지 한 번에 처리합니다.")

    with gr.Row():
        # Left: Chatbot
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="대화창", elem_classes="chatbot")
            msg_input = gr.Textbox(
                label="요청사항 입력",
                placeholder="예: 실용적인 30대 맘한테 라네즈 크림스킨 재구매하라고 문자 보내줘",
                lines=1,
                scale=4
            )
            submit_btn = gr.Button("전송", scale=1, variant="primary")
            clear = gr.ClearButton([msg_input, chatbot], scale=1)

        # Right: Dashboard (JSON/Status)
        with gr.Column(scale=1):
            gr.Markdown("### 📊 분석 대시보드 (Top-K Candidates)")
            json_output = gr.JSON(label="Intermediate Results (Input/Output details)")

    # Bind Enter Key
    msg_input.submit(
        fn=chat_handler,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot, json_output]
    )
    
    # Bind Button Click
    submit_btn.click(
        fn=chat_handler,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot, json_output]
    )

    print("Launching Chat UI on port 7868...")
    demo.launch(server_port=7868)
