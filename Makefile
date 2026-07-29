.PHONY: install run test lint check clean

install:
	python -m pip install -e ".[dev]"

run:
	python -m marketing_incrementality.cli run

test:
	python -m pytest

lint:
	python -m ruff check .

check: lint test
	python scripts/check_sensitive.py

clean:
	rm -rf data/generated .pytest_cache .ruff_cache
