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
    query = "30대 VIP 고객을 위한 설화수 크림 겨울 프로모션 문구 작성해줘"
    
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
    from services.crm_agent.data_loader import get_data_loader
    loader = get_data_loader()

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
        f.write("- **Source Data:** `data/crm_agent/persona_cards.jsonl` (Persona Definitions)\n")
        f.write(f"- **Input:** \"{query}\"\n")
        f.write(f"- **Output:**\n")
        f.write(f"  - Product: `{ip.get('target_product')}`\n")
        f.write(f"  - Persona: `{ip.get('target_persona')}`\n")
        f.write(f"  - Action ID: `{ip.get('selected_id')}`\n\n")
        
        # Retrieval
        ret = trace_data["retrieval"]
        f.write("### B. Retrieval\n")
        f.write("- **Source Data:** `data/rag_documents/product_cards.jsonl` (Product Database)\n")
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
        f.write("- **Source Data:** `data/crm_agent/brand_voice_guidelines.json` (Tone), `LLM` (Creative Content)\n")
        
        # Expand Context info
        target_persona = ip.get('target_persona')
        persona_info = loader.get_persona_info(target_persona)
        p_desc = persona_info.get("desc", "N/A")
        p_keys = ", ".join(persona_info.get("derived_keywords", [])[:5])
        
        action_id = ip.get('selected_id')
        action_hook = "N/A"
        if action_id:
             for ac in loader.action_cycles:
                if ac.get("id") == action_id:
                    action_hook = ac.get("core_guide", {}).get("messaging_hook") or ac.get("matching_description", "")
                    break
        
        # Brand Voice Summary
        brand_voice = loader.get_brand_voice(ret["products"][0]["brand"])
        tone_summary = ", ".join(brand_voice.get("tone_adjectives", []))

        f.write(f"- **Input:** Top Product, Persona(`{target_persona}`)\n")
        f.write(f"- **Context Expansion (Injected to Prompt):**\n")
        f.write(f"  - **Brand Voice Tone:** \"{tone_summary}\"\n")
        f.write(f"  - **Persona Description:** \"{p_desc}\"\n")
        f.write(f"  - **Persona Keywords:** \"{p_keys}\"\n")
        f.write(f"  - **Action Hook ({action_id}):** \"{action_hook}\"\n")
        
        # New: Product Details
        product_claims = "N/A"
        product_facts = "N/A"
        top_product_cand = None
        
        # Re-fetch full product data for the top candidate
        if ret and "products" in ret and ret["products"]:
            try:
                top_p_simple = ret["products"][0]
                print(f"[Trace] Top Product Simple: {top_p_simple}")
                
                 # Extract claims
                c_list = top_p_simple.get("claims", [])
                if isinstance(c_list, list) and c_list:
                    product_claims = ", ".join(c_list)
                
                 # Use existing retriever instance from orchestrator
                r = orch.retriever
                
                # Find product in retriever cache
                for pid, pdata in r.products.items():
                     if pdata["product_name"] == top_p_simple["name"]:
                         top_product_cand = pdata
                         print(f"[Trace] Found matching product: {pid}")
                         
                         # Build factsheet (require import)
                         from services.product_agent.factsheet import build_factsheet
                         
                         print("[Trace] Building Factsheet...")
                         fs = build_factsheet(pdata, r.news_data.get(pid))
                         print("[Trace] Factsheet built.")
                         
                         # Extract facts for report
                         raw_facts = fs.official_info.extracted_facts
                         processed_facts = []
                         processed_facts = []
                         for fact in raw_facts:
                            if isinstance(fact, str): processed_facts.append(fact)
                            elif isinstance(fact, dict): processed_facts.append(fact.get("fact") or fact.get("content") or str(fact))
                         product_facts = ", ".join(processed_facts[:5]) + "..." # Truncate for display
                         
                         # Construct Prompt
                         from services.crm_agent.prompt_engine import build_prompt
                         
                         # Brand Voice
                         bv = loader.get_brand_voice(top_p_simple["brand"])
                         print("[Trace] Building Prompt...")
                         
                         full_prompt = build_prompt(
                            product_name=pdata["product_name"],
                            brand_name=pdata["brand"],
                            factsheet=fs.dict(),
                            persona_name=target_persona,
                            action_id=action_id,
                            brand_voice=bv,
                            channel="문자(LMS)"
                         )
                         print("[Trace] Prompt built.")
                         
                         f.write(f"  - **Product Claims (Voice):** \"{product_claims}\"\n")
                         f.write(f"  - **Product Facts (Official):** \"{product_facts}\"\n")
                         
                         f.write(f"\n### E. Final System Prompt (Reconstructed)\n")
                         f.write(f"```text\n{full_prompt}\n```\n")
                         f.flush()
                         print("[Trace] Report Prompt section written.")
                         break
            except Exception as e:
                print(f"[Test Error] Failed to reconstruct prompt: {e}")
                with open("trace_error.log", "w") as errf:
                    import traceback
                    traceback.print_exc(file=errf)
                traceback.print_exc()

        f.write(f"\n- **Output (Draft):** (Refer to final message)\n\n")
        
        # Compliance
        f.write("### D. Compliance\n")
        f.write("- **Source Data:** `services/regulation_agent/compliance.py` (Logic), `data/rag_documents/regulation_rules.py` (Hypothetical)\n")
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
