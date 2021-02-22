.PHONY: black
black:
	poetry run black . --config=./pyproject.toml

.PHONY: build
build: test
	poetry build

.PHONY: install
install:
	poetry install

.PHONY: test
test: install black
	poetry run pytest tests/
