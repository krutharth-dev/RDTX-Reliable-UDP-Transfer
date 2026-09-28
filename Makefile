PYTHON ?= python3

.PHONY: help install web check test benchmark verify clean

help:
	@echo "RDTX VisualLab"
	@echo "  make install    Install project in editable mode"
	@echo "  make web        Start the local web dashboard"
	@echo "  make test       Run protocol + CLI + web tests"
	@echo "  make benchmark  Generate experiment benchmark files"
	@echo "  make verify     Run tests and benchmark"

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

clean:
	rm -rf received results visual_lab_data .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
