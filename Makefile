.PHONY: install run reproduce smoke test lint check clean

install:
	python -m pip install -e ".[dev]"

run:
	python -m marketing_incrementality.cli run

reproduce: run

smoke:
	python -m marketing_incrementality.cli run --customers 5000 --seed 7 --project-root /tmp/marketing-incrementality-smoke

test:
	python -m pytest

lint:
	python -m ruff check .

check: lint test smoke
	python scripts/check_sensitive.py

clean:
	rm -rf data/generated .pytest_cache .ruff_cache
