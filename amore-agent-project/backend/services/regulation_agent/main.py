from services.regulation_agent.compliance import get_compliance_agent

def main():
    agent = get_compliance_agent()
    
    # Test Case
    message = """
    (광고) [삼성물산] 주말 특가 안내 - 삼성물산 : 02-123-4567
    고객님, 이번 주말 전 품목 20% 할인 행사를 진행합니다.
    무료수신거부 080-1234-5678
    """
    
    print("--- Testing Message ---")
    print(message)
    
    result = agent.check_compliance(message)
    
    print("\n--- Result ---")
    print(f"Status: {result['status']}")
    print(f"Feedback: \n{result['feedback']}")

if __name__ == "__main__":
    main()
