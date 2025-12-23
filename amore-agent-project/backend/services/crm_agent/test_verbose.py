import sys
import os
import json

# -------------------------------------------------------------------------
# Path Configuration (to handle 'scripts-model1' folder name with hyphen)
# -------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Add 'backend' to path to import model_2
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

# Add 'scripts_model1' to path to import retriever directly OR just import from backend
# Since we are in backend/model_2, adding backend to path is enough.

from scripts_model1.retriever import get_retriever  # From scripts_model1
from model_2.generator import get_generator # From model_2
from model_2.data_loader import get_data_loader

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_verbose_pipeline():
    print_section("🚀 Amore CRM AI Agent: Engine Verification Step")
    
    # 0. User Input
    user_query = "라네즈 크림스킨 추천해줘"
    target_persona = "실용파 패밀리"
    action_purpose = "재구매 유도"
    
    print(f"[INPUT] User Query: '{user_query}'")
    print(f"[INPUT] Persona: '{target_persona}' (From UI Selection)")
    print(f"[INPUT] Purpose: '{action_purpose}' (From UI Selection)")
    
    # ---------------------------------------------------------------------
    # Step 1: Model-1 Retrieval
    # ---------------------------------------------------------------------
    print_section("STEP 1: Model-1 (Product Retriever)")
    print("Loading... (Source: backend/data/rag_documents/product_cards.jsonl)")
    
    retriever = get_retriever()
    candidates = retriever.retrieve(user_query)
    
    if not candidates:
        print("❌ No products found.")
        return

    top_cand = candidates[0]
    factsheet = top_cand.factsheet
    
    print(f"\n✅ [Output: Candidate #1]")
    print(f"   Name: {top_cand.product_name}")
    print(f"   Brand: {top_cand.brand}")
    print(f"   Score: {top_cand.score:.4f}")
    
    print(f"\n📄 [Factsheet Generated] (Source: Product Card + Heuristic Logic)")
    print(f"   Category: {factsheet.category}")
    print(f"   Key Claims: {factsheet.key_claims}")
    print(f"   Signals (Efficacy): {factsheet.signals.EFFICACY}")
    
    # ---------------------------------------------------------------------
    # Step 2: Context Loading (Model-2 Preparation)
    # ---------------------------------------------------------------------
    print_section("STEP 2: Context Loading (Model-2 Prep)")
    
    loader = get_data_loader()
    
    # Load Brand Tone
    brand_tone = loader.get_brand_tone(top_cand.brand)
    print(f"🔍 [Brand Tone] Source: scripts-model2/data/brand_tone_db.json")
    print(f"   Tone Voice: {brand_tone.get('tone_voice', 'Default')}")
    
    # Load Persona
    persona_info = loader.get_persona_info(target_persona)
    print(f"\n🔍 [Persona Context] Source: data/rag_documents/persona_cards.jsonl")
    print(f"   Desc: {persona_info.get('persona_description', 'N/A')}")
    print(f"   Keywords: {persona_info.get('derived_keywords', [])[:3]}...")
    
    # Load Action Cycle
    action_info = loader.get_action_info(action_purpose)
    print(f"\n🔍 [Action Cycle] Source: scripts-model2/data/action_cycle_db.json")
    print(f"   Strategy: {action_info.get('strategy', 'N/A')}")

    # ---------------------------------------------------------------------
    # Step 3: Prompt Engineering
    # ---------------------------------------------------------------------
    print_section("STEP 3: Prompt Construction")
    
    if not brand_tone or not persona_info or not action_info:
        print("⚠️ Warning: Some context data failed to load.")
    
    # We call generator internally calls prompt_engine, but let's visualize inputs 
    # The generator will combine these.
    print("Combining [Factsheet] + [Brand] + [Persona] + [Action] into LLM Prompt...")

    # ---------------------------------------------------------------------
    # Step 4: Generation (Model-2)
    # ---------------------------------------------------------------------
    print_section("STEP 4: Generation (Local LLM)")
    
    generator = get_generator()
    # Check if client is initialized (warning printed if key missing)
    if not generator.client:
         print("⚠️ OpenAI Client not initialized properly.")


    print("Generating Response... (This may take a moment)")
    response = generator.generate_response(
        product_cand=top_cand,
        persona_name=target_persona,
        action_purpose=action_purpose,
        channel="문자(LMS)"
    )
    
    print("\n" + "*"*60)
    print("🤖 [FINAL OUTPUT] Model-2 Response")
    print("*"*60)
    print(response)
    print("*"*60)

if __name__ == "__main__":
    test_verbose_pipeline()
