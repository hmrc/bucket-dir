.PHONY: black
black:
	poetry run black . --config=./pyproject.toml

.PHONY: build
build: test
	poetry build

.PHONY: init
init:
	pip install --upgrade poetry
	poetry install

.PHONY: publish
publish: build
	@poetry publish --username ${PYPI_USERNAME} --password ${PYPI_PASSWORD}

.PHONY: test
test: init black
	poetry run pytest tests/
