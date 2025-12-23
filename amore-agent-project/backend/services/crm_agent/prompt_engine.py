from typing import Dict, Any, List
from .data_loader import get_data_loader

def build_prompt(
    product_name: str,
    brand_name: str,
    factsheet: Dict[str, Any],
    persona_name: str,
    action_id: str,  # Changed from action_purpose string to specific ID
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
    
    # NEW: Fetch explicit action info by ID (if provided)
    action_info = {}
    if action_id and action_id != "NONE":
        for ac in loader.action_cycles:
            if ac["id"] == action_id:
                action_info = ac
                break
        # Fallback if ID was provided but not found
        if not action_info:
            action_info = {"name": action_id}
    
    # 2. Format Context Sections
    
    # [Brand Tone]
    tone_desc = brand_tone.get("tone_adjectives", ["친절한", "전문적인"])
    if isinstance(tone_desc, list):
        tone_str = ", ".join(tone_desc)
    else:
        tone_str = tone_desc
        
    voice_instruction = brand_tone.get("voice_instruction", "브랜드의 품격을 지키며 신뢰감을 주세요.")
    ending_style = brand_tone.get("ending_style", "정중한 해요체")

    # [Target Persona]
    p_desc = persona_info.get("persona_description", "일반 고객")
    p_keywords = ", ".join(persona_info.get("derived_keywords", [])[:5])
    
    # [Action / Context]
    context_guide = ""
    action_name = "일반 상품 소개" # Default name
    
    if action_info:
        situation = action_info.get("situation", "")
        keywords = action_info.get("keywords", [])
        writing_tip = action_info.get("core_guide", {}).get("writing_tip", "")
        
        if situation:
            context_guide += f"- 상황: {situation}\n"
        if keywords:
            kw_str = ", ".join(keywords)
            context_guide += f"- 필수 반영 키워드: {kw_str}\n"
        if writing_tip:
            context_guide += f"- 작성 팁: {writing_tip}\n"
            
        action_name = action_info.get("name", action_id)

    # [Product Factsheet]
    category = factsheet.get("category", "화장품")
    claims = ", ".join(factsheet.get("key_claims", []))
    usage = ", ".join(factsheet.get("usage", []))
    
    # 3. Construct System Prompt
    
    # Conditional guide section
    guide_section = ""
    if context_guide:
        guide_section = f"""
[CONTEXTUAL GUIDE]
{context_guide}
"""

    system_prompt = f"""
[ROLE]
너는 대한민국 뷰티 브랜드 '{brand_name}'의 CRM 마케터다.
아래 브랜드 페르소나와 가이드를 완벽하게 체화하여 메시지를 작성하라.

[BRAND VOICE]
- Tone & Manner: {tone_str}
- 말투(Ending): {ending_style}
- 지침: {voice_instruction}

[MANDATORY RULES]
1. 메시지의 첫 줄은 반드시 "(광고)"로 시작한다.
2. 의학적/치료적 효능(치료, 개선, 회복, 처방 등)을 암시하는 표현 절대 금지.
3. 과장된 표현(최고, 완벽, 100%, 즉시 등) 사용 금지.
4. 법적 고지·광고 표시를 생략하지 말 것.
{guide_section}
[TARGET PERSONA]
- 고객 성향: {p_desc}
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
- 핵심 소구점: {claims}

2. 발송 정보
- 채널: {channel}
- 목적: {action_name}

위 가이드와 *BRAND VOICE*를 반영하여, 고객의 마음을 움직이는 매력적인 카피를 작성해줘. (구조: [제목] / [본문])
"""

    return system_prompt.strip() + "\n\n" + user_input.strip()
