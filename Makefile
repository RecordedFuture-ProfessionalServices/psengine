FOLDERS=psengine tests examples docs

help:
	@echo "Available targets:"
	@echo " test      - run pytest"
	@echo " format    - run ruff format"
	@echo " lint      - run ruff check --fix"

test:
	@echo "Starting unit tests"
	@pytest tests_without_config
	@pytest --cov=psengine --cov-report html --cov-branch --cov-report term --random-order-bucket=module --cov-fail-under=95
	@coverage html

format:
	@ruff format $(FOLDERS)

lint:
	@ruff check $(FOLDERS) --fix

