# 1. 파이썬 3.10 슬림 버전
FROM python:3.10-slim

# 2. 작업 폴더 설정
WORKDIR /app

# 3. 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 코드 복사
COPY . .

# 5. 포트 열기 (Streamlit 기본 포트)
EXPOSE 8501

# 6. 헬스체크 (옵션: 스트림릿이 잘 떠있는지 확인용)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 7. 실행 명령
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]