# 1. 가볍고 안정적인 파이썬 3.10 슬림 버전 사용
FROM python:3.10-slim

# 2. 컨테이너 내 작업 폴더 설정
WORKDIR /app

# 3. 라이브러리 목록 파일 먼저 복사 (캐싱 효율을 위해)
COPY requirements.txt .

# 4. 라이브러리 설치 (캐시 사용 없이 가볍게 설치)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 코드 복사
COPY . .

# 6. 포트 열기 (FastAPI 기본 포트)
EXPOSE 8000

# 7. 서버 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]