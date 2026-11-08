# Python side: the designer API (port 8000), the Streamlit fallback app (port 8501), tests and reports.
# The Reonic data is confidential: it is NOT in the image. Mount it at /app/data (see docker-compose.yml).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/app/src
WORKDIR /app

# Dependencies first, so editing code does not reinstall them.
COPY pyproject.toml ./
COPY src ./src
RUN pip install -e ".[dev,analysis]"

COPY app.py ./
COPY scripts ./scripts
COPY tests ./tests

# Run as a normal user; models/ and reports/ are the only places we write.
RUN useradd --create-home --uid 1000 reonic && mkdir -p data models reports && chown -R reonic /app
USER reonic

EXPOSE 8000 8501
CMD ["uvicorn", "reonic.api:app", "--host", "0.0.0.0", "--port", "8000"]
