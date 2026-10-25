# Single-container build: API + built UI on :8000 (use deploy/docker-compose.yml for the 2-service setup)
FROM node:20-alpine AS ui
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/srv/data STATIC_DIR=/srv/static
WORKDIR /srv
COPY backend/pyproject.toml ./
COPY backend/src ./src
RUN pip install --no-cache-dir .
COPY backend/data ./data
COPY --from=ui /ui/dist ./static
RUN useradd -r -u 10001 app && chown -R app /srv
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/ready')"
CMD ["uvicorn", "windportal.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
