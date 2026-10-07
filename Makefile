PY ?= python3

.PHONY: all ingest transform analyze dashboard figures test clean

all: ingest transform analyze dashboard figures test

ingest:
	$(PY) src/ingest.py

transform:
	$(PY) src/transform.py

analyze:
	$(PY) src/analyze.py

dashboard:
	$(PY) src/dashboard.py

test:
	$(PY) -m pytest -q tests

clean:
	rm -rf data/raw/*.csv data/*.duckdb outputs/*

figures:
	$(PY) src/figures.py
