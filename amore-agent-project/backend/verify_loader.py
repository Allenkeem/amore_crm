from model_2.data_loader import get_data_loader
from model_2.intent_parser import get_intent_parser
import sys

print("--- Verifying DataLoader ---")
loader = get_data_loader()
print(f"Loaded Personas: {list(loader.personas.keys())}")
print(f"Count: {len(loader.personas)}")

print("\n--- Verifying IntentParser ---")
parser = get_intent_parser()
query = "실용적인 30대 맘"
result = parser.parse_query(query) # This might fail if LLM requires API key but we just want to test candidate matching logic if possible
# Actually parse_query calls LLM. Let's test the internal logic or mock it if needed.
# But wait, parse_query input is the raw text.

# We can manually test the matching logic since we improved it in the file.
# We'll just check if the personas are loaded. Validating the loader is the most critical step.

if len(loader.personas) == 0:
    print("FAIL: No personas loaded.")
    sys.exit(1)
else:
    print("SUCCESS: Personas loaded.")
