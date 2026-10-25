.PHONY: install test lint ingest demo-data api ui build docker docker-prod
install:   ; cd backend && pip install -e ".[dev]" && cd ../frontend && npm install
test:      ; cd backend && python -m pytest -q
lint:      ; cd backend && ruff check .
ingest:    ; cd backend && windportal ingest          # REAL Elexon data (needs internet)
demo-data: ; cd backend && windportal demo-data       # synthetic, offline
api:       ; cd backend && uvicorn windportal.main:app --reload --port 8000
ui:        ; cd frontend && npm run dev
build:     ; cd frontend && npm run build
docker:    ; docker compose up --build
docker-prod: ; docker compose -f deploy/docker-compose.yml up --build
