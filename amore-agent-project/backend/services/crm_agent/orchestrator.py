from typing import Dict, Any, List
# Import Modules
from services.product_agent.retriever import get_retriever
from services.crm_agent.generator import get_generator
from services.crm_agent.intent_parser import get_intent_parser
from services.crm_agent.data_loader import get_data_loader

class Orchestrator:
    def __init__(self):
        self.retriever = get_retriever()
        self.generator = get_generator()
        self.parser = get_intent_parser()
        
    def process_query(self, user_text: str) -> Dict[str, Any]:
        """
        Full Pipeline:
        1. Context Extraction (Intent Parser)
        2. Product Retrieval (Model-1)
        3. Message Generation (Model-2)
        """
        results = {
            "query": user_text,
            "parsed": None,
            "candidates": {},
            "final_message": None
        }
        
        # 1. Parse Intent
        parsed = self.parser.parse_query(user_text)
        results["parsed"] = parsed
        
        extracted = parsed["extracted"]
        product_query = extracted.get("product")
        target_persona = parsed["candidates"]["persona"][0] if parsed["candidates"]["persona"] else "Unknown"
        target_purpose = parsed["candidates"]["purpose"][0] if parsed["candidates"]["purpose"] else "Unknown"
        
        # 2. Retrieve Products (Model-1)
        # Use extracted product query or fallback to full text
        search_q = product_query if product_query else user_text
        product_cands = self.retriever.retrieve(search_q)
        
        # Serialize product candidates for UI
        serialized_products = []
        for p in product_cands[:3]: # Top 3
            serialized_products.append({
                "name": p.product_name,
                "brand": p.brand,
                "score": p.score,
                "claims": p.factsheet.key_claims
            })
        results["candidates"]["products"] = serialized_products
        results["candidates"]["personas"] = parsed["candidates"]["persona"]
        results["candidates"]["purposes"] = parsed["candidates"]["purpose"]
        
        # 3. Generate Message (Model-2)
        brand_tone_info = {}
        if product_cands:
            top_product = product_cands[0]
            # Fetch Brand Tone for UI
            brand_tone_info = self.retriever.loader.get_brand_tone(top_product.brand) if hasattr(self.retriever, 'loader') else get_data_loader().get_brand_tone(top_product.brand)
            
            # Initial Generation
            msg = self.generator.generate_response(
                product_cand=top_product,
                persona_name=target_persona,
                action_purpose=target_purpose,
                channel="문자(LMS)" # Default
            )
            
            # -----------------------------------------------------------------
            # FEEDBACK LOOP (Regulation Check)
            # -----------------------------------------------------------------
            audit_trail = []
            final_msg = msg
            
            # Import Regulation Agent lazily to avoid circular imports if any
            from services.regulation_agent.compliance import get_compliance_agent
            reg_agent = get_compliance_agent()
            
            max_retries = 3
            chk_result = None
            
            for attempt in range(max_retries + 1): # 0 to 3
                # Check Compliance
                chk_result = reg_agent.check_compliance(final_msg)
                
                # Record Audit
                audit_entry = {
                    "attempt": attempt + 1,
                    "message": final_msg,
                    "status": chk_result["status"],
                    "feedback": chk_result["feedback"]
                }
                audit_trail.append(audit_entry)
                
                if chk_result["status"] == "PASS":
                    break
                
                # If FAIL, refine (unless it's the last attempt)
                if attempt < max_retries:
                    print(f"[Orchestrator] Attempt {attempt+1} Failed. Refining...")
                    final_msg = self.generator.refine_response(
                        original_msg=final_msg,
                        feedback=chk_result["feedback"],
                        feedback_detail=f"Please fix the violations: {chk_result['feedback']}"
                    )
            
            results["final_message"] = final_msg
            results["audit_trail"] = audit_trail  # Expose to UI
            
        else:
            results["final_message"] = "죄송합니다. 검색된 상품이 없습니다. 상품명을 더 정확히 말씀해주시겠어요?"
            results["audit_trail"] = []
            
        results["candidates"]["detected_brand"] = brand_tone_info.get("brand_name", top_product.brand if product_cands else "Unknown")
        results["candidates"]["brand_tone"] = brand_tone_info.get("tone_voice", "Default")
            
        return results

_orch_instance = None
def get_orchestrator():
    global _orch_instance
    if _orch_instance is None:
        _orch_instance = Orchestrator()
    return _orch_instance
