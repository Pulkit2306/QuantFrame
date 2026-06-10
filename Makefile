# QuantFrame Makefile — Linux/macOS targets
# On Windows use WSL or run commands directly

.PHONY: all build-cpp test-cpp run-pipeline run-backend run-frontend \
        docker-up docker-down init-db test-python clean

# ── C++ Engine ──────────────────────────────────────────────────────────────
build-cpp:
	cmake -S layer2_engine -B layer2_engine/build -DCMAKE_BUILD_TYPE=RelWithDebInfo
	cmake --build layer2_engine/build --parallel

test-cpp: build-cpp
	cd layer2_engine/build && ctest --output-on-failure

# ── Python Pipeline ─────────────────────────────────────────────────────────
install-python:
	pip install -r layer1_pipeline/requirements.txt \
	            -r layer3_analytics/requirements.txt \
	            -r layer4_dashboard/backend/requirements.txt

init-db:
	python -m layer1_pipeline init-db

run-pipeline:
	python -m layer1_pipeline ingest

test-python:
	pytest layer1_pipeline/test_pipeline.py -v

# ── Layer 3 Analytics ───────────────────────────────────────────────────────
run-analytics:
	python -m layer3_analytics all-metrics 2023-01-01 2024-12-31

# ── Layer 4 Dashboard ───────────────────────────────────────────────────────
run-backend:
	uvicorn layer4_dashboard.backend.main:app --reload --port 8000

run-frontend:
	cd layer4_dashboard/frontend && npm install && npm run dev

# ── Docker ──────────────────────────────────────────────────────────────────
docker-up:
	docker compose up -d postgres backend

docker-down:
	docker compose down

# ── Misc ────────────────────────────────────────────────────────────────────
clean:
	rm -rf layer2_engine/build
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
