FROM python:3.11-slim AS cpp-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY backend/CMakeLists.txt ./backend/CMakeLists.txt
COPY backend/cpp_engine ./backend/cpp_engine
RUN cmake -S backend -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --config Release

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY --from=cpp-builder /src/build/bin/plagiarism_cli ./build/bin/plagiarism_cli

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\""]
