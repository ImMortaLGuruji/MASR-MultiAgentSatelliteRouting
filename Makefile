.PHONY: setup run test frontend clean

setup:
	pip install -r requirements.txt

run:
	python -m backend.main

test:
	python -m unittest discover -s tests -v

frontend:
	cd frontend && python -m http.server 5500

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
