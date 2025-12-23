from typing import Dict, Any, List
from .data_loader import get_data_loader

def build_prompt(
    product_name: str,
    brand_name: str,
    factsheet: Dict[str, Any],
    persona_name: str,
    action_purpose: str,
    channel: str = "문자(LMS)"
) -> str:
    """
    Constructs the full prompt for the LLM by combining:
    1. Product Factsheet (Model-1)
    2. Brand Tone (Data Loader)
    3. Target Persona (Data Loader)
    4. Action Cycle (Data Loader)
    """
    
    loader = get_data_loader()
    
    # 1. Fetch Contexts
    brand_tone = loader.get_brand_tone(brand_name)
    persona_info = loader.get_persona_info(persona_name)
    action_info = loader.get_action_info(action_purpose)
    
    # 2. Format Context Sections
    
    # [Brand Tone]
    tone_desc = brand_tone.get("tone_voice", "친절하고 전문적인")
    brand_guide = brand_tone.get("guidelines", [])
    brand_guide_str = "\n".join([f"- {g}" for g in brand_guide]) if brand_guide else "- 브랜드의 품격을 지키며 신뢰감을 주세요."

    # [Target Persona]
    p_desc = persona_info.get("persona_description", "일반 고객")
    p_keywords = ", ".join(persona_info.get("derived_keywords", [])[:5]) # Top 5 relevant keywords
    
    # [Action / Goal]
    goal = action_info.get("message_goal", action_purpose)
    strategy = action_info.get("strategy", "고객의 니즈에 맞춰 추천")
    
    # [Product Factsheet]
    category = factsheet.get("category", "화장품")
    claims = ", ".join(factsheet.get("key_claims", []))
    usage = ", ".join(factsheet.get("usage", []))
    
    # 3. Construct System Prompt (PATCH-M2-AD-SCAFFOLD-v1)
    system_prompt = f"""
[ROLE]
너는 대한민국 화장품 브랜드의 CRM 광고 메시지를 작성하는 AI다.
모든 출력은 '광고'로 간주된다.

[MANDATORY RULES]
1. 메시지의 첫 줄은 반드시 "(광고)"로 시작한다.
2. 의학적/치료적 효능을 암시하거나 단정하는 표현을 절대 사용하지 않는다.
   (예: 치료, 개선, 회복, 완화, 처방, 임상적으로 입증 → 금지)
3. 기능 표현은 반드시 '사용감', '도움', '느낌', '케어' 수준으로 한정한다.
4. 과장·최고·완벽·확실·즉시 효과 등의 단정적 표현을 금지한다.
5. 정보 제공형·권유형 톤을 유지하며, 판단은 소비자에게 남긴다.
6. 법적 고지·광고 표시를 임의로 생략하지 않는다.

[ALLOWED STYLE]
- 부드러운 CRM 톤
- 사용 상황 중심 설명
- 감각/루틴/경험 위주 서술
- 브랜드 톤: {tone_desc} ({brand_guide_str})
- 타겟 페르소나 Key: {p_keywords}

[OUTPUT CONSTRAINT]
- 위 규칙을 어길 경우 출력은 무효다.
"""

    # 4. Construct User Input
    user_input = f"""
---
[1. 대상 상품: {product_name}]
- 카테고리: {category}
- 핵심 소구 포인트: {claims}
- 사용법: {usage}

[2. 타겟 고객: {persona_name}]
- 성향: {p_desc}

[3. 발송 요청]
- 채널: {channel}
- 목적: {action_purpose}
---

위 정보를 바탕으로 고객에게 보낼 메시지 본문을 작성해줘. (구조: [제목] / [본문])
"""

    return system_prompt.strip() + "\n\n" + user_input.strip()
