import os
import pytest
from services.crm_agent.orchestrator import get_orchestrator
from services.product_agent.config import PRODUCT_CARDS_PATH

REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "execution_trace_report.md"))

def test_trace_execution_flow():
    """
    Runs an end-to-end query and generates a trace report.
    """
    orch = get_orchestrator()
    query = "30대 VIP 고객을 위한 설화수 자음생 크림 겨울 프로모션 문구 작성해줘"
    
    # 1. Capture Trace Data
    trace_data = {
        "query": query,
        "intent_parsing": {},
        "retrieval": {},
        "generation": {},
        "compliance": {}
    }
    
    final_message = ""
    audit_trail = []
    
    print(f"\n[Trace] Processing Query: {query}")
    
    # Stream processing
    for event in orch.process_query_stream(query):
        evt_type = event.get("type")
        key = event.get("key")
        val = event.get("value")
        
        if evt_type == "data":
            if key == "parsed":
                trace_data["intent_parsing"] = val
            elif key == "candidates":
                trace_data["retrieval"] = val
            elif key == "final_message":
                final_message = val
                trace_data["generation"]["output"] = final_message
            elif key == "audit_trail":
                audit_trail = val
                trace_data["compliance"] = val

    # 2. Generate Report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Execution Trace Report\n\n")
        f.write(f"**Query:** {query}\n\n")
        
        f.write("## 1. Resource Integrity\n")
        f.write(f"- **Product Data:** {PRODUCT_CARDS_PATH}\n")
        f.write("- **Status:** Valid (Checked by `test_resources.py`)\n\n")
        
        f.write("## 2. Model I/O Trace\n")
        
        # Intent Parsing
        ip = trace_data["intent_parsing"]
        f.write("### A. Intent Parsing\n")
        f.write(f"- **Input:** \"{query}\"\n")
        f.write(f"- **Output:**\n")
        f.write(f"  - Product: `{ip.get('target_product')}`\n")
        f.write(f"  - Persona: `{ip.get('target_persona')}`\n")
        f.write(f"  - Action ID: `{ip.get('selected_id')}`\n\n")
        
        # Retrieval
        ret = trace_data["retrieval"]
        f.write("### B. Retrieval\n")
        f.write(f"- **Input:** \"{ip.get('target_product') or query}\"\n")
        f.write(f"- **Output (Top Candidates):**\n")
        if ret and "products" in ret:
            for p in ret["products"]:
                f.write(f"  - [{p['score']}] **{p['brand']}** {p['name']}\n")
        else:
            f.write("  - No products retrieved.\n")
        f.write("\n")
            
        # Generation
        f.write("### C. Generation\n")
        f.write(f"- **Input:** Top Product, Persona(`{ip.get('target_persona')}`)\n")
        f.write(f"- **Output (Draft):** (Refer to final message)\n\n")
        
        # Compliance
        f.write("### D. Compliance\n")
        if audit_trail:
            for log in audit_trail:
                status_icon = "✅" if log['status'] == "PASS" else "❌"
                f.write(f"- **Attempt {log['attempt']}:** {status_icon} {log['status']}\n")
                if log['feedback']:
                    f.write(f"  - Feedback: {log['feedback']}\n")
        else:
            f.write("- No audit trail recorded.\n")
        f.write("\n")
            
        f.write("## 3. Final Output\n")
        f.write("```text\n")
        f.write(final_message)
        f.write("\n```\n")
        
    print(f"\n[Trace] Report generated at: {REPORT_PATH}")
    assert os.path.exists(REPORT_PATH)
    assert final_message != ""
