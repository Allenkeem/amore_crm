import sys
import os
import json

# Add parent of amore_crm (project root) to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from amore_crm.model_1.retriever import get_retriever

def main():
    print("Initializing Model-1 Retriever... (Loading Data)")
    retriever = get_retriever()
    print("Model-1 Ready! Type 'exit' to quit.\n")

    while True:
        user_query = input("User Query (e.g. '트러블 진정 앰플 추천'): ")
        if user_query.lower() in ["exit", "q", "quit"]:
            break
            
        print(f"\nSearching for: '{user_query}'...")
        results = retriever.retrieve(user_query)
        
        print(f"Top-{len(results)} Results:")
        for cand in results:
            print(f"-" * 40)
            print(f"[{cand.rank}] {cand.product_name}")
            print(f"    Brand: {cand.brand} (Score: {cand.score})")
            print(f"    Match: {cand.match.matched_entities} | {cand.match.matched_attributes}")
            print(f"    Category: {cand.factsheet.category}")
            print(f"    Key Claims: {cand.factsheet.key_claims}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
