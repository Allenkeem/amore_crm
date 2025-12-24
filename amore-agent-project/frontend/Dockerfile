# [Stage 1] Builder: 의존성 설치
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
# 가상환경에 라이브러리 설치
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# [Stage 2] Runner: 실제 실행
FROM python:3.10-slim AS runner
WORKDIR /app

# 기본 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# 보안을 위한 non-root 사용자 생성
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser

# 빌더 단계에서 설치한 가상환경만 쏙 가져오기
COPY --from=builder /opt/venv /opt/venv

# 소스 코드 복사 및 권한 부여
COPY . .
RUN chown -R appuser:appgroup /app

# 사용자 전환
USER appuser

EXPOSE 8501

# 헬스체크
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]