.PHONY: install run reproduce stability smoke test coverage lint build check clean

install:
	python -m pip install -e ".[dev]"

run:
	python -m marketing_incrementality.cli run

reproduce: run

stability:
	python -m marketing_incrementality.cli stability

smoke:
	python -m marketing_incrementality.cli run --customers 5000 --seed 7 --project-root /tmp/marketing-incrementality-smoke

test:
	python -m pytest

coverage:
	python -m pytest --cov=marketing_incrementality --cov-branch --cov-fail-under=90

lint:
	python -m ruff check .

build:
	python -m build --wheel --no-isolation

check: lint coverage build smoke
	python scripts/check_sensitive.py

clean:
	rm -rf data/generated .pytest_cache .ruff_cache
