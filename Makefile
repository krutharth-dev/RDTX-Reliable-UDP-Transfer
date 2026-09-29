PYTHON ?= python3

.PHONY: help install web check test benchmark verify demo-check clean

help:
	@echo "RDTX VisualLab"
	@echo "  make install      Install project in editable mode"
	@echo "  make web          Start the local web dashboard"
	@echo "  make check        Compile Python sources"
	@echo "  make test         Run protocol + CLI + web tests"
	@echo "  make benchmark    Generate experiment benchmark files"
	@echo "  make verify       Run tests and standard benchmark"
	@echo "  make demo-check   Run pre-evaluation readiness checks"
	@echo "  make clean        Remove local generated artifacts"

install:
	$(PYTHON) -m pip install -e .

web:
	$(PYTHON) -m webapp.app

check:
	$(PYTHON) -m compileall -q rdtx experiments webapp tests

test: check
	$(PYTHON) -m unittest discover -s tests -v

benchmark:
	$(PYTHON) -m rdtx benchmark

verify: test benchmark

demo-check: test
	$(PYTHON) -m rdtx --version
	$(PYTHON) -m rdtx benchmark --size-kib 8 --output /tmp/rdtx-demo-check.csv --markdown /tmp/rdtx-demo-check.md
	@test -s /tmp/rdtx-demo-check.csv
	@test -s /tmp/rdtx-demo-check.md
	@echo "RDTX demo readiness: PASS"

clean:
	rm -rf received results visual_lab_data .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
