from typing import Dict, Any, List
from .data_loader import get_data_loader

def build_prompt(
    product_name: str,
    brand_name: str,
    factsheet: Dict[str, Any],
    persona_name: str,
    action_id: str,
    brand_voice: Dict[str, Any] = None,
    channel: str = "문자(LMS)"
) -> str:
    """
    Constructs the full prompt for the LLM by combining:
    1. Product Factsheet (Model-1)
    2. Brand Voice (Data Loader)
    3. Target Persona (Data Loader)
    4. Action Cycle (Data Loader)
    """
    
    loader = get_data_loader()
    
    # 1. Fetch Contexts
    # Brand Voice is passed in or fetched fallback
    if not brand_voice:
        brand_voice = loader.get_brand_voice(brand_name)
        
    persona_info = loader.get_persona_info(persona_name)
    
    # Action Info by ID
    action_info = {}
    if action_id:
        for ac in loader.action_cycles:
            if ac.get("id") == action_id:
                action_info = ac
                break
    
    # 2. Format Context Sections
    
    # [Brand Voice]
    # Default Tone if voice not found
    tone_desc = brand_voice.get("tone_adjectives", ["친절한", "전문적인"])
    if isinstance(tone_desc, list):
        tone_str = ", ".join(tone_desc)
    else:
        tone_str = tone_desc
        
    voice_instruction = brand_voice.get("voice_instruction", "브랜드의 품격을 지키며 신뢰감을 주세요.")
    ending_style = brand_voice.get("ending_style", "정중한 해요체")
    do_not_rules = brand_voice.get("do_not", "과장된 표현 금지")

    # [Target Persona]
    p_desc = persona_info.get("persona_description", "일반 고객")
    p_keywords = ", ".join(persona_info.get("derived_keywords", [])[:5])
    
    # [Action / Goal]
    # Use 'messaging_hook' as the primary guide for generation
    action_name = action_info.get("name", action_id)
    messaging_hook = action_info.get("core_guide", {}).get("messaging_hook", "")
    writing_tip = action_info.get("core_guide", {}).get("writing_tip", "")
    
    # [Product Factsheet]
    category = factsheet.get("category", "화장품")
    
    # Handle Nested Structure
    official = factsheet.get("official_info", {})
    voice = factsheet.get("voice_info", {})
    if hasattr(factsheet, "official_info"): 
        official = factsheet.official_info.dict()
        voice = factsheet.voice_info.dict()

    claims = ", ".join(voice.get("key_claims", []))
    usage = ", ".join(voice.get("usage", []))
    
    raw_facts = official.get("extracted_facts", [])
    processed_facts = []
    for f in raw_facts:
        if isinstance(f, str):
            processed_facts.append(f)
        elif isinstance(f, dict):
             processed_facts.append(f.get("fact") or f.get("content") or str(f))
    facts = ", ".join(processed_facts)

    # 3. Construct System Prompt
    system_prompt = f"""
[ROLE]
너는 대한민국 뷰티 브랜드 '{brand_name}'의 전문 CRM 마케터다.
아래 브랜드 보이스와 가이드를 철저히 준수하여 메시지를 작성하라.

[BRAND VOICE]
- Tone & Manner: {tone_str}
- 말투(Ending): {ending_style}
- 지침: {voice_instruction}
- 주의사항(DO NOT): {do_not_rules}

[MANDATORY RULES]
1. 메시지의 첫 줄은 반드시 "(광고)"로 시작한다.
2. 메시지 끝부분에는 반드시 "무료수신거부" 문구를 포함한다. (예: [수신거부: 무료 080-1234-5678])
3. 전송자의 명칭과 연락처를 반드시 포함한다.
4. 의학적/치료적 효능(치료, 개선, 회복, 처방, 부작용 없음 등)을 암시하는 표현 절대 금지.
5. 과장된 표현(최고, 완벽, 100%, 즉시 등) 사용 금지.
6. 제공된 [공식 정보]와 [소구 포인트]를 기반으로 작성하며, 거짓 정보를 생성하지 않음.

[ACTION GUIDE (IMPORTANT)]
- 목적: {action_name}
- **핵심 소구(Hook)**: {messaging_hook}
- 작성 팁: {writing_tip}

[TARGET PERSONA]
- 성향: {p_desc}
- 관심 키워드: {p_keywords}
"""

    # 4. Construct User Input
    user_input = f"""
---
[작업 요청]
다음 상품에 대한 CRM 메시지를 작성해줘.

1. 상품 정보
- 상품명: {product_name}
- 카테고리: {category}
- 공식 정보(Facts): {facts}
- 핵심 소구(Review): {claims}
- 사용법: {usage}

2. 발송 정보
- 채널: {channel}

위 가이드와 **BRAND VOICE**를 완벽하게 반영하여, 고객의 마음을 움직이는 매력적인 카피를 작성해줘. (구조: [제목] / [본문])
"""

    return system_prompt.strip() + "\n\n" + user_input.strip()
