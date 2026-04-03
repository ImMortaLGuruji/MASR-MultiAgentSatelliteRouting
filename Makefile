.PHONY: setup run test frontend clean

setup:
	pip install -e .

run:
	python -m backend.main

test:
	python -m unittest discover -s tests -v

frontend:
	cd frontend && npm install && npm run dev

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name "node_modules" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
