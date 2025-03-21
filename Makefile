.PHONY: bandit
bandit:
	poetry run bandit --recursive --exclude ./tests/ .

.PHONY: black
black:
	poetry run black . --config=./pyproject.toml

.PHONY: build
build: test bandit
	poetry build

.PHONY: init
init:
	pip install --upgrade poetry
	poetry install

.PHONY: profile
profile:
	export BUCKET_DIR_PROFILE_TEST=yes; poetry run pytest --profile-svg --no-cov tests/test_bucket_dir.py::test_generate_bucket_dir_big_bucket

.PHONY: publish
publish: build
	@poetry config repositories.upload "https://artefacts.tax.service.gov.uk/artifactory/api/pypi/pips/"
	@poetry config http-basic.upload ${PYPI_USERNAME} ${PYPI_PASSWORD}
	@poetry publish --repository upload

.PHONY: test
test: init black
	poetry run pytest tests/

.PHONY: update
update: init
	poetry update
