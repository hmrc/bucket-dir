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
	@echo publish step skipped see PBD-4265

.PHONY: test
test: init black
	poetry run pytest tests/

.PHONY: update
update: init
	poetry update
