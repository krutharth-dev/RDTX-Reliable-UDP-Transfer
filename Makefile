PYTHON ?= python3

.PHONY: help check test demo-receive demo-send demo-lossy clean

help:
	@echo "RDTX developer commands"
	@echo "  make check         Compile Python sources"
	@echo "  make test          Run the complete test suite"
	@echo "  make demo-receive  Start a localhost receiver"
	@echo "  make demo-send     Send demo.txt"
	@echo "  make demo-lossy    Send demo.txt with 25% simulated packet loss"
	@echo "  make clean         Remove generated caches and received files"

check:
	$(PYTHON) -m compileall -q rdtx tests

test: check
	$(PYTHON) -m unittest discover -s tests -v

demo-receive:
	$(PYTHON) -m rdtx receive --port 9000 --output-dir received --trace

demo-send:
	$(PYTHON) -m rdtx send demo.txt --host 127.0.0.1 --port 9000 --trace

demo-lossy:
	$(PYTHON) -m rdtx send demo.txt --host 127.0.0.1 --port 9000 --loss 0.25 --seed 10 --trace

clean:
	rm -rf received .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
