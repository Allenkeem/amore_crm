import pytest
from services.crm_agent.intent_parser import get_intent_parser
from services.regulation_agent.compliance import get_compliance_agent

def test_intent_parser_structure():
    """Verify Intent Parser returns correct structure."""
    parser = get_intent_parser()
    query = "설화수 자음생 크림 프로모션 문구 써줘"
    result = parser.parse_query(query)
    
    assert "target_product" in result
    assert "target_persona" in result
    assert "selected_id" in result
    assert "candidates" in result

def test_compliance_check_pass():
    """Verify compliance agent passes safe message."""
    agent = get_compliance_agent()
    safe_msg = "이 제품은 설화수의 베스트셀러입니다. (광고)"
    result = agent.check_compliance(safe_msg)
    
    assert result["status"] == "PASS"

def test_compliance_check_fail():
    """Verify compliance agent fails on unsafe keywords (missing ad tag)."""
    agent = get_compliance_agent()
    unsafe_msg = "이 제품은 설화수의 베스트셀러입니다." # Missing (광고)
    result = agent.check_compliance(unsafe_msg)
    
    assert result["status"] == "FAIL"
    assert "광고 표기 누락" in result["feedback"] or "광고" in result["feedback"]
