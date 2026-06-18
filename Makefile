# DataGov Agent - Makefile
# En Windows sin `make`, usa los comandos equivalentes del README.

.PHONY: help install data validate test lint format api ui milvus-up milvus-down clean

help:
	@echo "Targets disponibles:"
	@echo "  install      Instala dependencias en el entorno activo"
	@echo "  data         Genera los datasets sinteticos"
	@echo "  validate     Valida detecciones vs known_issues_expected.json"
	@echo "  test         Ejecuta la suite de pruebas (sin Ollama ni Docker)"
	@echo "  lint         Ejecuta ruff"
	@echo "  format       Aplica black + ruff --fix"
	@echo "  api          Levanta el backend FastAPI"
	@echo "  ui           Levanta la interfaz Streamlit"
	@echo "  milvus-up    Levanta Milvus via docker compose"
	@echo "  milvus-down  Detiene Milvus"

install:
	pip install -r requirements.txt

data:
	python data/synthetic/generate_synthetic_data.py

validate:
	python scripts/validate_dataset.py

test:
	pytest

lint:
	ruff check app tests

format:
	black app tests
	ruff check --fix app tests

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

ui:
	streamlit run ui/streamlit_app.py --server.port 8510

milvus-up:
	docker compose up -d

milvus-down:
	docker compose down

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__
