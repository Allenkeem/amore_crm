import gradio as gr
import json
import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 1. 경로 설정 및 모듈 로드
# ─────────────────────────────────────────────────────────────────────────────
current_dir = Path(__file__).resolve().parent
# backend 폴더
sys.path.append(str(current_dir)) 
# backend/src 폴더 (핵심 fix)
sys.path.append(str(current_dir / "src")) 
# 프로젝트 루트 (sogang_chatbot - chatbot.py 로드를 위해)
sys.path.append(str(current_dir.parent)) 

try:
    # src가 경로에 추가되었으므로 'core.crm_agent'로 바로 접근 가능
    from core.crm_agent import AP_CRMAgent
except ImportError:
    # 혹시 기존 방식(src.core...)으로 시도
    try:
        from src.core.crm_agent import AP_CRMAgent
    except ImportError as e:
        print(f"[UI] Import Error: {e}")
        # 디버깅을 위해 현재 sys.path 출력
        print(f"[DEBUG] sys.path: {sys.path}")
        print("Please run this script from the 'backend' folder.")
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 2. 데이터 로드 및 초기화
# ─────────────────────────────────────────────────────────────────────────────

# 에이전트 생성
agent = AP_CRMAgent(data_dir=str(current_dir / "data/processed"), device="cpu")

# UI 선택지용 데이터 로드 helper
def load_keys_from_json(filename):
    path = current_dir / "data/processed" / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [item["name"] for item in data]
            return list(data.keys())
    except:
        return []

product_list = load_keys_from_json("fact_db.json")
persona_list = load_keys_from_json("persona_db.json")
action_list = load_keys_from_json("action_cycle_db.json")

# ─────────────────────────────────────────────────────────────────────────────
# 3. 로직 핸들러
# ─────────────────────────────────────────────────────────────────────────────

def handle_generation(product, persona, action_dropdown, channel, custom_goal):
    if not product:
        return "⚠️ 상품을 먼저 선택해주세요."
    
    # 발신 목적: 드롭다운 선택값 우선, 없으면 사용자 직접 입력값 사용
    final_goal = action_dropdown if action_dropdown else custom_goal
    if not final_goal:
        return "⚠️ 발신 목적(시나리오)을 선택하거나 직접 입력해주세요."

    return agent.generate_marketing_message(
        product_name=product,
        persona_name=persona,
        action_purpose=final_goal,
        channel=channel
    )

# ─────────────────────────────────────────────────────────────────────────────
# 4. Gradio UI (Styling & Layout)
# ─────────────────────────────────────────────────────────────────────────────

custom_css = """
body { font-family: 'Pretendard', sans-serif !important; background-color: #f8f9fa; }
.header-area { margin-bottom: 2rem; text-align: center; }
.header-title { font-size: 2rem; font-weight: 700; color: #1a1a1a; margin-bottom: 0.5rem; }
.header-desc { color: #666; font-size: 1rem; }
.input-panel { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; }
.output-panel { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; min-height: 400px; }
#gen-btn { background: #000 !important; color: white !important; font-weight: bold; border-radius: 8px; height: 50px; font-size: 1.1rem; }
#gen-btn:hover { background: #333 !important; }
"""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="AmorePacific CRM Agent") as demo:
    
    with gr.Column(elem_classes="header-area"):
        gr.HTML("""
        <div class="header-title">AP Marketing AI Agent</div>
        <div class="header-desc">Deep Context RAG 기반의 초개인화 메시지 생성 솔루션</div>
        """)

    with gr.Row():
        # ──────────────── Left: Control Panel ────────────────
        with gr.Column(scale=1, elem_classes="input-panel"):
            gr.Markdown("### 🛠️ 캠페인 설계")
            
            input_product = gr.Dropdown(
                label="📦 대상 상품", 
                choices=product_list, 
                value=product_list[0] if product_list else None,
                info="Fact/Review DB에서 정보를 가져옵니다."
            )
            
            input_persona = gr.Dropdown(
                label="🎯 타겟 페르소나", 
                choices=persona_list,
                value=persona_list[0] if persona_list else None,
                info="고객 성향에 맞춰 톤앤매너를 자동 조정합니다."
            )
            
            input_action = gr.Dropdown(
                label="🔄 발신 시나리오 (자동 추천)",
                choices=action_list,
                value=action_list[0] if action_list else None,
                allow_custom_value=True,
                info="구매 주기별 최적 전략을 선택하세요."
            )
            
            input_custom_goal = gr.Textbox(
                label="📝 (선택) 직접 입력",
                placeholder="예: 비오는 날 감성 문자 보내줘",
                visible=True
            )
            
            input_channel = gr.Radio(
                label="📢 발송 채널",
                choices=["앱푸시 (Push)", "알림톡 (Kakao)", "LMS (문자)", "인스타그램"],
                value="앱푸시 (Push)"
            )

            gr.Markdown("---")
            btn_generate = gr.Button("✨ 메시지 생성하기", elem_id="gen-btn")

        # ──────────────── Right: Preview Panel ────────────────
        with gr.Column(scale=1, elem_classes="output-panel"):
            gr.Markdown("### 💬 생성 결과")
            output_display = gr.Markdown(
                value="왼쪽에서 옵션을 선택하고 **[생성하기]** 버튼을 눌러주세요.",
                latex_delimiters=[]
            )
            
            # 심의 규제 결과 (Dummy Placeholder)
            with gr.Accordion("⚖️ 광고 심의 규제 검수 결과 (Simulated)", open=False):
                gr.Markdown("✅ **검수 통과**: 금지 표현('최고', '완치')이 발견되지 않았습니다.\n(추후 PDF RAG 연동 예정)")

    # 동작 연결
    btn_generate.click(
        fn=handle_generation,
        inputs=[input_product, input_persona, input_action, input_channel, input_custom_goal],
        outputs=output_display
    )

if __name__ == "__main__":
    print("Launching UI...")
    demo.launch(server_name="0.0.0.0", server_port=8080)
