from services.product_agent.retriever import get_retriever

def main():
    print("Initializing ProductRetriever...")
    retriever = get_retriever()
    
    # Test Query 1 (Known to work before)
    query1 = "설화수 수분 크림"
    print(f"\n--- Testing Query: {query1} ---")
    results1 = retriever.retrieve(query1)
    if results1:
        print(f"Found {len(results1)} products.")
        print(f"Top 1: {results1[0].product_name} (Score: {results1[0].score})")
    else:
        print("Found 0 products (UNEXPECTED).")
        
    # Test Query 2 (Generic)
    query2 = "30대 선물 추천"
    print(f"\n--- Testing Query: {query2} ---")
    results2 = retriever.retrieve(query2)
    if results2:
        print(f"Found {len(results2)} products.")
    else:
        print("Found 0 products.")

if __name__ == "__main__":
    main()
