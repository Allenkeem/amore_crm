from .config import SYSTEM_PROMPT_TEMPLATE, LLM_MODEL
from .retrieval import RetrievalEngine
from .data_loader import get_regulation_dbs

class ComplianceAgent:
    def __init__(self):
        print("[RegulationAgent] Initializing...")
        self.retriever = RetrievalEngine()
        self.spam_db, self.cosmetics_db = get_regulation_dbs()
        
    def _run_single_check(self, crm_message, run_id):
        """Internal function for a single pass"""
        print(f"  > [RegulationAgent] Run {run_id}: Generating queries and validating...")
        
        # 1. Retrieve Context
        context = self.retriever.get_combined_context(
            crm_message, self.spam_db, self.cosmetics_db
        )
        
        # 2. Construct Prompt
        user_prompt = f"""
        Context Regulations (Source of Truth):
        {context}
        
        CRM Message (SMS/LMS):
        {crm_message}
        
        Check for violations significantly strictly based on Context.
        """
        
        response = self.retriever.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content

    def check_compliance(self, crm_message: str) -> dict:
        """
        Double-Check Logic.
        Returns Dict: {
            "status": "PASS" | "FAIL",
            "reason": str (Summary of failure or pass),
            "feedback": str (Detailed text including suggestion),
            "run_1_result": str,
            "run_2_result": str
        }
        """
        print("[RegulationAgent] Analyzing message with Dual-Pass Logic...")
        
        # Run 1
        result1 = self._run_single_check(crm_message, 1)
        
        final_status = "PASS"
        detected_run = 0
        final_feedback = result1
        result2 = "Skipped (Run 1 Passed)"

        if "[실패]" in result1:
             # Run 1 Failed -> Fail Immediately
            final_status = "FAIL"
            detected_run = 1
            final_feedback = result1
            # Optional: Run 2 to double check? No, Fail is Fail.
        else:
            # Run 1 Passed -> Check Optimisation
            # Original Logic: Must run both
            # Patch 6-1 Logic: If Run 1 PASS, Trust it (or skip to save cost)
            # However, for safety, let's stick to the user request: "IF 1차 검사 PASS: 2차 검사 SKIP"
            pass 
            
        # Re-evaluating based on "Conservatism". 
        # User said: "Current: PASS인데도 2차 검사 실행 금지" 
        # So we implement exactly that.
        
        print(f"\n[Final Verdict]: {final_status}")
        
        return {
            "status": final_status,
            "feedback": final_feedback,
            "run_details": {
                "run_1": result1,
                "run_2": result2
            }
        }

_agent_instance = None
def get_compliance_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ComplianceAgent()
    return _agent_instance
