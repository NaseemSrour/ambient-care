# Single-image deploy: build the Flutter PWA, then run FastAPI which serves
# both the API and the built PWA. Works on Render, Railway, Fly.io, or any
# Docker host.

# ---- Stage 1: build the Flutter web app ----
FROM ghcr.io/cirruslabs/flutter:stable AS flutter
WORKDIR /app/frontend
COPY frontend/pubspec.yaml frontend/pubspec.lock ./
RUN flutter pub get
COPY frontend/ ./
RUN flutter build web --release

# ---- Stage 2: Python runtime ----
FROM python:3.12-slim AS runtime
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# Place the built PWA exactly where app/main.py looks for it.
COPY --from=flutter /app/frontend/build/web /app/frontend/build/web

# Persist the SQLite database on a mounted volume in production.
ENV AC_DATABASE_PATH=/data/ambient_care.db
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
