import sys
import os
import json

# Add current dir to path to import amore_crm
# Add parent of amore_crm (project root) to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from amore_crm.model_1.retriever import get_retriever

def test():
    retriever = get_retriever()
    
    queries = [
        "라네즈 크림 스킨",
        "트러블 진정 앰플 추천해줘",
        "설화수 윤조에센스",
        "비레디 쿠션"
    ]
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        results = retriever.retrieve(q)
        for cand in results:
            print(f"[{cand.rank}] {cand.product_name} (Score: {cand.score})")
            print(f"   Matches: {cand.match}")
            print(f"   Category: {cand.factsheet.category}, Claims: {cand.factsheet.key_claims[:3]}")

if __name__ == "__main__":
    test()
