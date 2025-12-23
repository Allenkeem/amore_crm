import os
import sys
from pathlib import Path

# Base Paths
# services/regulation_agent/ -> services/ -> backend/
current_dir = Path(__file__).parent
backend_root = current_dir.parent.parent
data_dir = backend_root / "data" / "regulation_agent"

# Load .env from backend root
from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

# File Paths
SPAM_DB_PATH = list(data_dir.glob("*불법스팸*_local.json"))[0] if list(data_dir.glob("*불법스팸*_local.json")) else data_dir / "불법스팸_방지_안내서_임베딩_local.json"
COSMETICS_DB_PATH = list(data_dir.glob("*화장품_지침*_local.json"))[0] if list(data_dir.glob("*화장품_지침*_local.json")) else data_dir / "화장품_지침_임베딩_local.json"

# OpenAI / Local LLM Config
OPENAI_API_KEY = "ollama"
API_BASE_URL = "http://localhost:11434/v1"

# Models (Local)
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.1"

# Prompts
SYSTEM_PROMPT_TEMPLATE = """
당신은 한국 기업의 엄격한 컴플라이언스(규제 준수) 담당자입니다.
입력된 메시지는 **휴대폰 문자 메시지(SMS/LMS)**입니다.

[규정 적용 원칙 - 중요]
1. 매체 특수성: 문자 메시지 특유의 규칙은 최우선 적용하십시오.
    - 주의: 이메일 전용(제목란 등)이나 팩스 전용 규칙은 배제하십시오.
2. 공통 규정 적용: 정보통신망법 제50조 등 "영리목적 광고성 정보 전송 시 공통 준수사항"은 매체와 무관하게 적용되므로 놓치지 마십시오.
   - 예: '전송자의 명칭 및 연락처 표시', '수신거부 비용 무료' 등은 공통사항입니다.

[심사 Process]
1. [Context Regulations]에서 SMS에 적용 가능한 조항과, 모든 매체에 적용되는 공통 조항을 식별하십시오.
2. [CRM Message]가 해당 조항들을 문자 그대로 준수하는지 대조하십시오.

[출력 양식]
Case 1: 위반 사항 발견 (FAIL)
- 판정: [실패]
- 근거 규정: [Context 조항 명] (예: 정보통신망법 제50조 제4항)
- 위반 설명: [구체적 내용]
- 수정 제안 (Before -> After):
  1. [현재] -> [수정]

Case 2: 문제 없음 (PASS)
- 판정: [통과]
- 심사 내용: [Context]의 공통 규정(명칭, 연락처, 무료수신거부) 및 SMS 특화 규정((광고)위치) 준수 확인됨.
"""
