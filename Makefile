.PHONY: black
black:
	poetry run black . --config=./pyproject.toml

.PHONY: install
install:
	poetry install

.PHONY: test
test: install black
	poetry run pytest tests/
