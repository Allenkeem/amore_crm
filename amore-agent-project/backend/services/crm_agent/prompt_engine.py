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
    
    # 3. Construct System Prompt
    system_prompt = f"""
당신은 아모레퍼시픽의 수석 CRM 카피라이터입니다.
아래 제공된 [상품 정보], [타겟 페르소나], [브랜드 톤], [발송 목적]을 완벽하게 조합하여, 고객에게 보낼 최적의 마케팅 메시지를 작성하세요.

[지침]
1. **브랜드 톤**: '{brand_name}'의 톤앤매너({tone_desc})를 엄격히 준수하세요.
   {brand_guide_str}
2. **페르소나 맞춤**: 타겟인 '{persona_name}'({p_desc})가 반응할 키워드({p_keywords})를 자연스럽게 녹여내세요.
3. **목적 달성**: 이번 메시지의 목적은 '{goal}'입니다.전략: {strategy}
4. **채널 최적화**: '{channel}' 채널 특성에 맞는 길이와 이모지를 사용하세요.
5. **거짓 정보 금지**: 제공된 팩트시트에 없는 효능을 지어내지 마세요.
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
