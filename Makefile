PYTHON ?= python3

.PHONY: help check test benchmark verify demo-receive demo-send demo-lossy demo-reorder clean

help:
	@echo "RDTX developer commands"
	@echo "  make check         Compile Python sources"
	@echo "  make test          Run the complete test suite"
	@echo "  make benchmark     Generate CSV + Markdown experiment results"
	@echo "  make verify        Run tests and benchmark together"
	@echo "  make demo-receive  Start a localhost receiver with packet tracing"
	@echo "  make demo-send     Send demo.txt with packet tracing"
	@echo "  make demo-lossy    Send demo.txt with 25% simulated packet loss"
	@echo "  make demo-reorder  Send demo.txt with explicit packet reordering"
	@echo "  make clean         Remove generated caches, received files and results"

check:
	$(PYTHON) -m compileall -q rdtx tests experiments

test: check
	$(PYTHON) -m unittest discover -s tests -v

benchmark:
	$(PYTHON) -m rdtx benchmark

verify: test benchmark

demo-receive:
	$(PYTHON) -m rdtx receive --port 9000 --output-dir received --trace

demo-send:
	$(PYTHON) -m rdtx send demo.txt --host 127.0.0.1 --port 9000 --trace

demo-lossy:
	$(PYTHON) -m rdtx send demo.txt --host 127.0.0.1 --port 9000 --loss 0.25 --seed 10 --trace

demo-reorder:
	$(PYTHON) -m rdtx send demo.txt --host 127.0.0.1 --port 9000 --reorder 1.0 --seed 10 --trace

clean:
	rm -rf received results .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
