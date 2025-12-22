import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# 외부 의존성 (경로 문제시 조정 필요)
import sys
import os

# 현재 파일 위치 기준 프로젝트 루트 경로 추가
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parents[2]  # backend/src/core -> backend/ -> sogang_chatbot/
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 기존 챗봇 모듈 재사용 (Backend 내부 복사본 활용)
try:
    from src.utils.legacy_chatbot import load_llm
except ImportError:
    # 경로 문제시 상대 경로 시도
    try:
        from utils.legacy_chatbot import load_llm
    except ImportError:
        # 최후의 수단: sys.path 경로 기반 import
        from backend.src.utils.legacy_chatbot import load_llm


class AP_CRMAgent:
    """
    아모레퍼시픽 CRM 마케팅 에이전트 (Backend Core)
    - 5개 DB(Fact, Review, Persona, Action, Brand)를 통합 활용하여 메시지 생성
    """
    
    def __init__(self, data_dir: str = "backend/data/processed", device: str = "cpu"):
        self.data_dir = Path(data_dir)
        self.device = device
        
        print(f"[CRM Agent] Initializing... (Data: {self.data_dir}, Device: {self.device})")
        
        # 1. Load All Databases
        self.db = {
            "fact": self._load_json("fact_db.json"),
            "review": self._load_json("review_db.json"),
            "persona": self._load_json("persona_db.json"),
            "action": self._load_json("action_cycle_db.json"),
            "brand": self._load_json("brand_tone_db.json"),
        }
        
        # 2. Load LLM
        print(f"[CRM Agent] Loading LLM Model...")
        self.llm = load_llm(device=self.device)
        print("[CRM Agent] Ready.")

    def _load_json(self, filename: str) -> Dict[str, Any] | list:
        path = self.data_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[WARN] DB file not found: {path} (Initializing empty)")
            return {}
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
            return {}

    def _find_brand_tone(self, product_name: str) -> Dict[str, Any]:
        """상품명에서 브랜드를 추론하여 톤앤매너 정보 반환"""
        brand_db = self.db["brand"]
        
        # 1. Exact/Partial Match in DB Keys
        for brand_key, info in brand_db.items():
            # DB 키가 "LANEIGE" 등 영문일 수 있으므로, info 안의 한글 이름도 체크
            if brand_key in product_name.upper():
                return info
            if info.get("brand_name", "").split("(")[0].strip() in product_name:
                return info
                
        # 2. Fallback
        return brand_db.get("general", {})

    def _find_item_in_list_db(self, db_key: str, search_key: str, match_field: str) -> Dict[str, Any]:
        """리스트 형태 DB(Persona, Action)에서 ID나 이름으로 항목 찾기"""
        data_list = self.db.get(db_key, [])
        for item in data_list:
            if item.get(match_field) == search_key or item.get("name") == search_key:
                return item
        return {}
    
    def generate_marketing_message(
        self, 
        product_name: str, 
        persona_name: str, 
        action_purpose: str,
        channel: str
    ) -> str:
        
        # ─────────────────────────────────────────────────────────────
        # Phase 1: Context Retrieval (정보 수집)
        # ─────────────────────────────────────────────────────────────
        
        # 1. Product Info (Fact & Review)
        fact_info = self.db["fact"].get(product_name, {})
        review_info = self.db["review"].get(product_name, {})
        
        if not fact_info and not review_info:
            return "❌ 오류: 해당 상품 정보를 찾을 수 없습니다. (DB에 상품명이 정확한지 확인해주세요)"

        # 2. Persona Info
        # UI에서 "혜택 중시형 (가성비 헌터)" 처럼 들어오므로 매칭 로직 필요
        persona_info = {}
        for p in self.db["persona"]:
            if p["name"] in persona_name or persona_name in p["name"]:
                persona_info = p
                break
        
        # 3. Action Cycle (Purpose)
        action_info = {}
        # UI 입력값(자유 텍스트)과 DB의 stage_name 매칭 시도, 실패시 텍스트 그대로 사용
        for a in self.db["action"]:
            if a["stage_name"] in action_purpose:
                action_info = a
                break
        
        # 4. Brand Tone
        brand_info = self._find_brand_tone(product_name)

        # ─────────────────────────────────────────────────────────────
        # Phase 2: Prompt Engineering (프롬프트 조립)
        # ─────────────────────────────────────────────────────────────
        
        system_prompt = f"""
당신은 아모레퍼시픽의 수석 CRM 카피라이터입니다.
주어진 [상품 정보], [타겟 페르소나], [브랜드 톤]을 완벽하게 조합하여, 
고객의 구매 욕구를 자극하는 마케팅 메시지를 작성하세요.

[필수 지침]
1. **톤앤매너 준수**: '{brand_info.get('brand_name')}' 브랜드의 보이스({brand_info.get('tone_voice')})를 반드시 유지하세요.
2. **페르소나 맞춤**: 타겟 고객인 '{persona_info.get('name')}'가 반응할만한 키워드({', '.join(persona_info.get('keywords', []))})를 포함하세요.
3. **목적 달성**: 이번 메시지의 목적은 '{action_info.get('message_goal', action_purpose)}'입니다.
4. **거짓 정보 금지**: 제공된 상품 스펙(Fact)에 없는 내용은 지어내지 마세요.
5. **형식 준수**: 채널({channel}) 특성에 맞는 길이와 포맷을 사용하세요.
"""

        user_input_context = f"""
---
[1. 대상 상품: {product_name}]
- 핵심 카피: {review_info.get('one_line_copy', '')}
- 주요 혜택/스펙: {fact_info.get('content_details', {}).get('special_bens', '')}
- 고객 리뷰 요약: {review_info.get('marketing_points', {})}

[2. 타겟 페르소나: {persona_info.get('name', persona_name)}]
- 성향: {persona_info.get('description', '')}
- 가이드: {persona_info.get('tone_guidance', '')}

[3. 발송 시나리오: {action_info.get('stage_name', action_purpose)}]
- 전략: {action_info.get('strategy', '')}
- 참고 템플릿: {action_info.get('example_templates', [])}

[4. 발송 채널]
- {channel} (이모지 적절히 사용, 가독성 높게)
---

위 정보를 바탕으로 다음 형식에 맞춰 메시지를 작성해줘.

**[제목]**
(고객의 눈길을 끄는 20자 이내 카피)

**[본문]**
(줄바꿈을 활용하여 가독성 좋게, 300자 이내)
"""

        full_prompt = system_prompt + "\n" + user_input_context
        
        # ─────────────────────────────────────────────────────────────
        # Phase 3: Generation (생성)
        # ─────────────────────────────────────────────────────────────
        
        try:
            # LLM 호출 (chatbot.py의 파이프라인 활용)
            # max_new_tokens를 넉넉히 줌
            generated = self.llm(
                full_prompt, 
                max_new_tokens=512, 
                do_sample=True, 
                temperature=0.75,
                top_p=0.9
            )
            
            result_text = generated[0]["generated_text"]
            
            # 프롬프트 부분 제거 (Echo 방지)
            if result_text.startswith(full_prompt):
                result_text = result_text[len(full_prompt):].strip()
                
            return result_text
            
        except Exception as e:
            traceback.print_exc()
            return f"⚠️ 메시지 생성 중 오류 발생: {e}"

# 테스트 코드
if __name__ == "__main__":
    agent = AP_CRMAgent(data_dir=str(Path(project_root) / "backend/data/processed"))
    print("\n>>> TEST GENERATION <<<")
    print(agent.generate_marketing_message(
        "라네즈 크림스킨", 
        "혜택 중시형", 
        "장바구니 이탈", 
        "앱푸시"
    ))
