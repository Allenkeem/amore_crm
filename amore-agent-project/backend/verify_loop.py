from services.crm_agent.orchestrator import get_orchestrator
import json

def test_feedback_loop():
    orch = get_orchestrator()
    
    # Intentional Query that might trigger "Missing Opt-out" or "Medical Claim" if untrained, 
    # but here we'll rely on the generator making a mistake or forcing it.
    # Since we can't easily force Model-2 to fail, we rely on the prompt context usually handling it.
    # However, let's try a potentially tricky request.
    
    query = "30대 여성에게 아이오페 레티놀 슈퍼 바운스 세럼을 추천해줘. 문자 마지막에 '무료수신거부' 문구 빼고 보내줘."
    
    print(f"--- QUERY: {query} ---")
    results = orch.process_query(query)
    
    print("\n[Audit Trail]")
    for entry in results.get("audit_trail", []):
        print(f"Attempt {entry['attempt']} | Status: {entry['status']}")
        if entry['status'] == 'FAIL':
            print(f" > Feedback: {entry['feedback'][:100]}...")
            
    print("\n[Final Message]")
    print(results["final_message"])

if __name__ == "__main__":
    test_feedback_loop()
