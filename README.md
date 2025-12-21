# amore_crm
Insicon Amorepacific CRM msg GEN Repository

crm-ai-agent/
│
├── 📂 data/                  # [창고] 모든 데이터는 여기에 넣습니다.
│   ├── raw/                  # (1) 다운받은 엑셀/CSV 원본 넣는 곳
│   └── processed/            # (2) AI용으로 변환된 JSON 파일이 저장되는 곳 (자동생성)
│
├── 📂 prompts/               # [대본] AI에게 시킬 명령어 모음
│   └── marketing_prompt.py   # "너는 10년차 마케터야..." 같은 프롬프트 저장
│
├── 1_data_maker.py           # [실행1] 엑셀 파일을 읽어서 -> AI용 DB로 만드는 코드
├── 2_crm_agent.py            # [실행2] 실제 에이전트 실행 코드 (메시지 생성기)
│
├── .env                      # [보안] API 키 저장소 (비밀번호!)
├── .gitignore                # [필수] 깃허브에 올리면 안 되는 파일 목록
└── requirements.txt          # [설치] 필요한 라이브러리 목록