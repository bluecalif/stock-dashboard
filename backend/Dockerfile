FROM python:3.12-slim

WORKDIR /app

# 1단계: 의존성 설치 (pyproject.toml 변경 시에만 재실행)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 2단계: 소스 코드 복사 (항상 최신)
COPY alembic.ini .
COPY collector/ collector/
COPY research_engine/ research_engine/
COPY api/ api/
COPY db/ db/
COPY config/ config/

# editable 재설치 (fast — egg-link만 생성)
RUN pip install --no-cache-dir -e . --no-deps

EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
