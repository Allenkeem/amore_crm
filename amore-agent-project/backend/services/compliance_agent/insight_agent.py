print("Starting Insight Agent...")
import sys
import io

# Force UTF-8 for stdout/stderr to prevent encoding errors on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
try:
    print("Importing os...")
    import os
    print("Importing json...")
    import json
    print("Importing numpy...")
    import numpy as np
    print("Importing gradio (this may take a moment)...")
    import gradio as gr
    print("Importing openai...")
    from openai import OpenAI
    print("Importing sklearn...")
    from sklearn.metrics.pairwise import cosine_similarity
    print("Importing getpass...")
    import getpass
except ImportError as e:
    print("\n" + "="*50)
    print("❌ ERROR: 필수 라이브러리가 설치되지 않았습니다.")
    print(f"상세 에러: {e}")
    print("해결 방법: 터미널에 아래 명령어를 입력하여 설치해주세요:")
    print("python -m pip install gradio openai scikit-learn numpy")
    print("="*50 + "\n")
    sys.exit(1)

# -------------------------------------------------------------------------
# Path Setup
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print("Importing Orchestrator...")

# Import Orchestrator (Product + CRM Agent)
from services.crm_agent.orchestrator import get_orchestrator

# -------------------------------------------------------------------------
# Compliance Validator Class (Refactored from Notebook)
# -------------------------------------------------------------------------
class ComplianceValidator:
    def __init__(self, spam_db_path, cosmetics_db_path):
        self.client = self._setup_openai()
        self.spam_db = self._load_db(spam_db_path)
        self.cosmetics_db = self._load_db(cosmetics_db_path)
        print(f"Loaded Spam DB: {len(self.spam_db)} chunks")
        print(f"Loaded Cosmetics DB: {len(self.cosmetics_db)} chunks")

    def _setup_openai(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback for local testing if env not set
             print("Warning: OPENAI_API_KEY not found in env.")
        return OpenAI(api_key=api_key)

    def _load_db(self, path):
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_embedding(self, text, model="text-embedding-3-small"):
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input=[text], model=model).data[0].embedding

    def retrieve_top_k(self, query_embedding, db, k=5):
        if not db:
            return []
        
        db_embeddings = [item['embedding'] for item in db]
        similarities = cosine_similarity([query_embedding], db_embeddings)[0]
        
        # Get top-k indices
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "score": similarities[idx],
                "metadata": db[idx]['metadata']
            })
        return results

    def generate_legal_queries(self, crm_message):
        prompt = f"""
        Analyze the CRM message and generate 3 specific legal search queries.
        Goal: Retrieve rules that apply to SMS/LMS, but ALSO common rules for all advertising media (e.g., Article 50).
        
        CRM Message:
        {crm_message}
        
        Generate concise queries for:
        1. SMS-specific marking requirements (Opt-out, Sender ID).
        2. Common advertising prohibitions (False/Exaggerated claims, common to all media).
        3. Product-specific restrictions (e.g., Cosmetics medical claims).
        
        Output List only.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        queries = response.choices[0].message.content.strip().split("\n")
        return [q.split(". ")[-1] for q in queries if q.strip()]

    def get_combined_context(self, message):
        search_queries = self.generate_legal_queries(message)
        print(f"[Compliance] Generated Queries: {search_queries}")
        
        all_spam_docs = []
        all_cosmetics_docs = []
        
        # Retrieve for EACH query
        for q in search_queries:
            q_vec = self.get_embedding(q)
            all_spam_docs.extend(self.retrieve_top_k(q_vec, self.spam_db, k=3))
            all_cosmetics_docs.extend(self.retrieve_top_k(q_vec, self.cosmetics_db, k=3))
            
        # Also retrieve for original message
        original_vec = self.get_embedding(message)
        all_spam_docs.extend(self.retrieve_top_k(original_vec, self.spam_db, k=3))
        all_cosmetics_docs.extend(self.retrieve_top_k(original_vec, self.cosmetics_db, k=3))
        
        # Deduplicate
        def deduplicate(docs):
            unique_docs = []
            seen_headers = set()
            for doc in docs:
                key = doc['metadata']['header'] + doc['metadata']['content'][:30]
                if key not in seen_headers:
                    unique_docs.append(doc)
                    seen_headers.add(key)
            return unique_docs

        final_spam_docs = deduplicate(all_spam_docs)
        final_cosmetics_docs = deduplicate(all_cosmetics_docs)
        
        context_text = f"-- [Regulation 1: Spam Prevention & IT Network Act (Total {len(final_spam_docs)})] --\n"
        for doc in final_spam_docs:
            context_text += f"Header: {doc['metadata']['header']}\nContent: {doc['metadata']['content']}\n\n"
            
        context_text += f"\n-- [Regulation 2: Cosmetics Guidelines (Total {len(final_cosmetics_docs)})] --\n"
        for doc in final_cosmetics_docs:
            context_text += f"Header: {doc['metadata']['header']}\nContent: {doc['metadata']['content']}\n\n"
            
        return context_text

    def _run_single_check(self, crm_message, run_id):
        print(f"  > [Compliance] Run {run_id}: Validating...")
        context = self.get_combined_context(crm_message)
        
        system_prompt = """
        당신은 한국 기업의 엄격한 컴플라이언스(규제 준수) 담당자입니다.
        입력된 메시지는 **휴대폰 문자 메시지(SMS/LMS)**입니다.
        
        [규정 적용 원칙 - 중요]
        1. 매체 특수성: 문자 메시지 특유의 규칙은 최우선 적용하십시오.
            - 주의: 이메일 전용(제목란 등)이나 팩스 전용 규칙은 배제하십시오.
        2. 공통 규정 적용: 정보통신망법 제50조 등 "영리목적 광고성 정보 전송 시 공통 준수사항"은 매체와 무관하게 적용되므로 놓치지 마십시오.
           - 예: '전송자의 명칭 및 연락처 표시', '수신거부 비용 무료' 등은 공통사항입니다.
        
        [심사 Process]
        1. [Context Regulations]에서 SMS에 적용 가능한 조항과, 모든 매체에 적용되는 공통 조항을 식별하십시오.
        2. [CRM Message]가 해당 조항들을 문자 그대로 준수하는지 대조하십시오.
        
        [출력 양식]
        Case 1: 위반 사항 발견 (FAIL)
        - 판정: [실패]
        - 근거 규정: [Context 조항 명] (예: 정보통신망법 제50조 제4항)
        - 위반 설명: [구체적 내용]
        - 수정 제안 (Before -> After):
          1. [현재] -> [수정]
        
        Case 2: 문제 없음 (PASS)
        - 판정: [통과]
        - 심사 내용: [Context]의 공통 규정(명칭, 연락처, 무료수신거부) 및 SMS 특화 규정((광고)위치) 준수 확인됨.
        """
        
        user_prompt = f"""
        Context Regulations (Source of Truth):
        {context}
        
        CRM Message (SMS/LMS):
        {crm_message}
        
        Check for violations significantly strictly based on Context.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content

    def check_compliance(self, crm_message):
        # Double Check Logic
        result1 = self._run_single_check(crm_message, 1)
        
        if "[실패]" in result1:
             return result1, False
        
        result2 = self._run_single_check(crm_message, 2)
        if "[실패]" in result2:
            return result2, False
            
        return result1, True

# -------------------------------------------------------------------------
# Application Initialization
# -------------------------------------------------------------------------
print("Initializing Orchestrator...")
orch = get_orchestrator()

print("Initializing Compliance Validator...")
# Absolute paths to data
base_data_path = os.path.join(current_dir, "data", "compliance_agent")
spam_db_path = os.path.join(base_data_path, "불법스팸_방지_안내서_임베딩.json")
cosmetics_db_path = os.path.join(base_data_path, "화장품_지침_임베딩.json")

validator = ComplianceValidator(spam_db_path, cosmetics_db_path)

# -------------------------------------------------------------------------
# Main Logic (Pipeline)
# -------------------------------------------------------------------------
def pipeline_handler(user_message, history):
    if not user_message:
        return history, "", "", ""

    # 1. Product + CRM Agent Generation
    print(">>> Step 1: Generating Message...")
    gen_results = orch.process_query(user_message)
    generated_msg = gen_results.get("final_message", "Error generation message.")
    
    # Extract details for UI
    candidates = gen_results.get("candidates", {})
    products = candidates.get("products", [])
    top_product = products[0].get("name", "None") if products else "없음"
    detected_brand = candidates.get("detected_brand", "Unknown")
    top_persona = candidates.get("personas", [])[0] if candidates.get("personas") else "없음"

    bot_response_summary = f"""
    ✅ **생성 완료**
    - 제품: {top_product} ({detected_brand})
    - 타겟: {top_persona}
    """
    
    # 2. Compliance Validation
    print(">>> Step 2: Validating Compliance...")
    report, is_pass = validator.check_compliance(generated_msg)
    
    status_icon = "🟢" if is_pass else "🔴"
    status_text = "PASS (안전)" if is_pass else "FAIL (위반 발견)"
    
    compliance_summary = f"""
    ### {status_icon} Compliance Status: {status_text}
    
    {report}
    """
    
    # Update History
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_response_summary + "\n\n(우측 패널에서 상세 결과를 확인하세요.)"})
    
    return history, generated_msg, compliance_summary, gen_results

# -------------------------------------------------------------------------
# UI Layout (Dashboard Style)
# -------------------------------------------------------------------------
custom_css = """
body { font-family: 'Pretendard', sans-serif !important; background-color: #f8f9fa; }
.header-area { text-align: center; margin-bottom: 1rem; }
.chatbot { height: 500px !important; overflow-y: auto; }
.panel-header { font-weight: bold; font-size: 1.1em; margin-bottom: 0.5rem; }
"""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="Insight Agent (Unified)") as demo:
    
    with gr.Column(elem_classes="header-area"):
        gr.Markdown("## 💎 Insight AI Agent (Product + CRM + Compliance)")
        gr.Markdown("고객 맞춤형 메시지 생성부터 법적 리스크 진단까지 한 번에 처리합니다.")

    with gr.Row():
        # Left Column: Chat Interface
        with gr.Column(scale=1):
            gr.Markdown("### 💬 Agent Chat")
            chatbot = gr.Chatbot(label="대화창", elem_classes="chatbot", type="messages")
            msg_input = gr.Textbox(
                label="요청사항 입력",
                placeholder="예: 30대 여성에게 라네즈 크림스킨 프로모션 문자 써줘",
                lines=2
            )
            with gr.Row():
                submit_btn = gr.Button("전송 (Generate & Check)", variant="primary")
                clear_btn = gr.ClearButton([msg_input, chatbot])

        # Right Column: Analysis Dashboard
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Analysis Dashboard")
            
            with gr.Group():
                gr.Markdown("<div class='panel-header'>📝 Generated CRM Message (Draft)</div>")
                txt_generated_msg = gr.TextArea(label="생성된 메시지 초안", lines=8, interactive=False)
            
            with gr.Group():
                gr.Markdown("<div class='panel-header'>⚖️ Compliance Report</div>")
                txt_compliance_report = gr.Markdown(label="컴플라이언스 리포트")
                
            with gr.Accordion("🔍 Debug Info (Internal JSON)", open=False):
                json_debug = gr.JSON()

    # Event Binding
    submit_btn.click(
        fn=pipeline_handler,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, txt_generated_msg, txt_compliance_report, json_debug]
    )
    
    msg_input.submit(
        fn=pipeline_handler,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, txt_generated_msg, txt_compliance_report, json_debug]
    )

    print("Launching Insight Agent on port 7875...")
    demo.launch(server_port=7875)
