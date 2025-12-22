import streamlit as st
import requests

# 백엔드 주소 (로컬 테스트 시 localhost, 도커 사용 시 서비스명)
# 도커 컴포즈 사용 시 'http://backend:8000'으로 변경해야 함
BACKEND_URL = "http://localhost:8000/generate" 

st.set_page_config(page_title="Amore Mall Marketing Agent", layout="wide")

st.title("💄 아모레몰 마케팅 메시지 생성 에이전트")
st.markdown("---")

# 화면을 좌우 2개 컬럼으로 분할 (입력창 / 결과창)
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. 설정 입력")
    
    # 요구사항: 5~10개의 페르소나 정의
    persona_options = [
        "20대 사회초년생 (가성비 중시)",
        "30대 직장인 (피부 관리/안티에이징 관심)",
        "40대 주부 (가족용 제품 구매)",
        "트렌드 민감형 코덕 (신상 위주)",
        "럭셔리 선호 VIP (고가 라인)",
        "비건/클린뷰티 선호 고객"
    ]
    selected_persona = st.selectbox("고객 페르소나 선택", persona_options)

    # 브랜드 톤 & 목적 설정
    tone = st.radio("메시지 톤(Tone)", ["친근하고 감성적인", "전문적이고 신뢰가는", "활기차고 재치있는"], horizontal=True)
    purpose = st.text_input("메시지 발송 목적", placeholder="예: 설날 선물세트 프로모션, 신상 립스틱 출시 알림")

    generate_btn = st.button("메시지 생성하기", type="primary")

with col2:
    st.header("2. 생성 결과")
    
    if generate_btn:
        if not purpose:
            st.warning("메시지 발송 목적을 입력해주세요.")
        else:
            with st.spinner("AI가 고객 맞춤 메시지를 작성 중입니다..."):
                try:
                    # 백엔드로 데이터 전송
                    payload = {
                        "persona": selected_persona,
                        "tone": tone,
                        "purpose": purpose
                    }
                    response = requests.post(BACKEND_URL, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 결과 보여주기 (카드 형태)
                        st.success("생성 완료!")
                        st.subheader("📌 제목 (40자 이내)")
                        st.info(result['title'])
                        
                        st.subheader("📝 본문 (350자 이내)")
                        st.text_area("메시지 내용", value=result['content'], height=200)
                    else:
                        st.error("서버 통신 오류가 발생했습니다.")
                except Exception as e:
                    st.error(f"연결 실패: {e}")
                    st.caption("백엔드 서버가 켜져 있는지 확인해주세요.")