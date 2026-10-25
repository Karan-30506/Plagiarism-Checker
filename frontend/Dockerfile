FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/frontend
COPY frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

COPY frontend ./

EXPOSE 8501
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port \"${PORT:-8501}\""]
