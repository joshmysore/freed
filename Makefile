.PHONY: setup run test scan fmt lint clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  setup    - Install dependencies"
	@echo "  run      - Start FastAPI server"
	@echo "  test     - Run tests"
	@echo "  scan     - Run CLI scan"
	@echo "  fmt      - Format code with black and isort"
	@echo "  lint     - Lint code with ruff"
	@echo "  clean    - Clean up generated files"
	@echo "  help     - Show this help message"

setup:
	pip install -r requirements.txt

run:
	cd src && python app.py

test:
	pytest tests/ -v

scan:
	cd src && python cli.py

fmt:
	black src/ tests/
	isort src/ tests/

lint:
	ruff check src/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.ics" -delete
	find . -type f -name "token.json" -delete
