.PHONY: run test clean

run:
	./run.sh

test:
	.venv/bin/python -m pytest tests/

clean:
	rm -rf __pycache__ .pytest_cache dist build *.spec