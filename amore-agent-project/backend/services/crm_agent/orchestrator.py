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
        
    def process_query_stream(self, user_text: str, history: List[Dict[str, str]] = []):
        """
        Streaming Pipeline (Generator)
        Yields dicts: {"type": "status"|"data", ...}
        """
        
        # 1. Parse Intent
        yield {"type": "status", "msg": "고객님의 의도를 분석하고 있어요... 🧐"}
        parsed = self.parser.parse_query(user_text)
        yield {"type": "data", "key": "parsed", "value": parsed}
        
        extracted = parsed["extracted"]
        product_query = extracted.get("product")
        target_persona = parsed["candidates"]["persona"][0] if parsed["candidates"]["persona"] else "Unknown"
        target_purpose = parsed["candidates"]["purpose"][0] if parsed["candidates"]["purpose"] else "Unknown"
        
        # 2. Retrieve Products (Model-1)
        yield {"type": "status", "msg": "적합한 상품과 혜택을 찾고 있어요... 📦"}
        
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
                "claims": p.factsheet.voice_info.key_claims
            })
            
        # Send candidates data immediately
        candidates_data = {
            "products": serialized_products,
            "personas": parsed["candidates"]["persona"],
            "purposes": parsed["candidates"]["purpose"],
            "detected_brand": "Unknown", # Will update
            "brand_tone": "Default"      # Will update
        }
        
        # 3. Generate Message (Model-2)
        yield {"type": "status", "msg": "매력적인 메시지를 작성하고 있어요... ✍️"}
        
        brand_tone_info = {}
        if product_cands:
            top_product = product_cands[0]
            # Fetch Brand Tone
            brand_tone_info = self.retriever.loader.get_brand_tone(top_product.brand) if hasattr(self.retriever, 'loader') else get_data_loader().get_brand_tone(top_product.brand)
            
            # Update candidates with brand info and send
            candidates_data["detected_brand"] = brand_tone_info.get("brand_name", top_product.brand)
            candidates_data["brand_tone"] = brand_tone_info.get("tone_voice", "Default")
            yield {"type": "data", "key": "candidates", "value": candidates_data}
            
            # Initial Generation
            msg = self.generator.generate_response(
                product_cand=top_product,
                persona_name=target_persona,
                action_purpose=target_purpose,
                channel="문자(LMS)", # Default
                history=history # Pass History
            )
            
            # -----------------------------------------------------------------
            # FEEDBACK LOOP (Regulation Check)
            # -----------------------------------------------------------------
            yield {"type": "status", "msg": "규제 위반 여부를 꼼꼼히 점검 중이에요... 👮"}
            
            audit_trail = []
            final_msg = msg
            
            # Import Regulation Agent lazily
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
                    yield {"type": "status", "msg": f"규제 위반 발견! 수정 중입니다... ({attempt+1}/{max_retries}) 🔧"}
                    
                    print(f"[Orchestrator] Attempt {attempt+1} Failed. Refining...")
                    final_msg = self.generator.refine_response(
                        original_msg=final_msg,
                        feedback=chk_result["feedback"],
                        feedback_detail=f"Please fix the violations: {chk_result['feedback']}"
                    )
            
            # Final Result
            yield {"type": "data", "key": "final_message", "value": final_msg}
            yield {"type": "data", "key": "audit_trail", "value": audit_trail}
            
            # -----------------------------------------------------------------
            # DYNAMIC SUGGESTIONS (Post-Generation)
            # -----------------------------------------------------------------
            yield {"type": "status", "msg": "추가 제안을 생각하고 있어요... 💡"}
            print("[Orchestrator] Calling generate_suggestions...")
            suggestions = self.generator.generate_suggestions(
                original_msg=final_msg,
                product_name=top_product.product_name,
                target_persona=target_persona
            )
            print(f"[Orchestrator] Yielding suggestions: {suggestions}")
            yield {"type": "data", "key": "suggestions", "value": suggestions}
            
            yield {"type": "data", "key": "suggestions", "value": suggestions}
            
        else:
            # 2-B. Fallback: General Conversation Mode
            # Instead of "Sorry", generate a natural response
            yield {"type": "status", "msg": "💬 답변을 생각하고 있어요..."}
            
            candidates_data["detected_brand"] = None
            candidates_data["brand_tone"] = None
            yield {"type": "data", "key": "candidates", "value": candidates_data}
            
            # Generate General Response
            gen_response = self.generator.generate_general_chat(user_text)
            
            yield {"type": "data", "key": "final_message", "value": gen_response}
            yield {"type": "data", "key": "audit_trail", "value": []}
            
            # Fallback suggestions for general chat
            yield {"type": "data", "key": "suggestions", "value": ["설화수 신제품 보여줘", "마케팅 문구 추천해줘", "라네즈 이벤트 알려줘"]}
            
        yield {"type": "status", "msg": "완료되었습니다! ✨"}

_orch_instance = None
def get_orchestrator():
    global _orch_instance
    if _orch_instance is None:
        _orch_instance = Orchestrator()
    return _orch_instance
