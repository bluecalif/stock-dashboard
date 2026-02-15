FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY alembic.ini .
COPY collector/ collector/
COPY research_engine/ research_engine/
COPY api/ api/
COPY db/ db/
COPY config/ config/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
