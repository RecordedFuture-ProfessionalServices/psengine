VERSION := $(shell grep -E "^version = " pyproject.toml | cut -d '"' -f2)
VERSION_FILE := psengine/_version.py
EXAMPLES_DIR := examples
PREV_VERSION := $(shell grep "version" psengine/_version.py | cut -d "'" -f 2)

FOLDERS=psengine psengine_cli tests examples docs/source
BANNER_PATTERN = "TERMS OF USE"

# Commands
CWD := $(shell pwd)
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTHON_VERSION := python3.10
UNAME := $(shell uname)
VIRTUALENV := $(shell command -v virtualenv 2> /dev/null)
FORMAT := ruff format
CHECK := ruff check 
TYPOS := $(shell command -v typos 2>/dev/null || echo "/opt/typos/typos")

# MacOSX & Unix support
SED := sed
ifeq ($(UNAME),Darwin)
SED:= sed -i ''
else
SED:= sed -i
endif

.PHONY: format review rev syntaxfix clean clear_cache
.PHONY: help debug test unittests examples typo
.PHONY: setup build build_module
.PHONY: confluence

debug:
	@echo "PSEngine Version:" $(VERSION)
	@echo "Python Version: ";  $(PYTHON) -V
	@echo "Installed Packages:"
	@$(PIP) list

help:
	@echo "Available targets:"
	@echo " debug          - display debug information"
	@echo " setup          - setup development environment"
	@echo " test           - run review and unittests"
	@echo " unittests      - run nosetests to perform unittests"
	@echo " examples       - run all test apps"
	@echo " format         - run ruff format"
	@echo " syntaxfix      - run ruff check --fix"
	@echo " rev		       - run ruff check --fix and ruff format"
	@echo " review         - run ruff check and ruff format"
	@echo " build          - build pythom module (output in ./dist)"
	@echo " imports_check  - check import do not start with psengine"
	@echo " banner_check   - check the banner is present at the top of each psengine file"
	@echo " banner         - apply the banner is present at the top of each psengine file"
	@echo "Miscellaneous targets:"
	@echo " clean         - delete build and packaging artifacts"
	@echo " clear_cache   - remove python pycache and pytest_cache"
	@echo " confluence    - build confluence documentation"
	@echo " artifcatory   - copy psengine in main repo ready to be pushed in artifactory"

##########################################
#
# Targets related to development environment setup
#
##########################################
setup:
	@echo "Setting up development environment"
    ifndef VIRTUALENV
		@echo "Creating virtual environment using $(PYTHON_VERSION)"
		@$(PYTHON_VERSION) -m venv venv
    else
		@echo "Creating virtual environment using virtualenv for $(PYTHON_VERSION)"
		@virtualenv venv -p $(PYTHON_VERSION)
    endif
	
	@echo "Installing dependencies..."
	@. $(CWD)/venv/bin/activate && $(PIP) install -e $(CWD)/.'[dev]'
	@echo "Success! Development environment is ready"
	@echo "Please activate the virtual env with: source venv/bin/activate"

##########################################
#
# Targets related to versioning:
#  - psengine/_version.py
#
##########################################
version_bump:
	@echo "Bumping version to $(VERSION)"
	@ $(SED) "/__version__ = / s/__version__ = [^,]*/__version__ = '$(VERSION)'/" $(VERSION_FILE)

##########################################
#
# Targets related to build
#
##########################################
build: clear_cache version_bump format build_module clean clear_cache 

build_module:
	@echo "Building python module"
	@$(PYTHON) -m build 
	@echo "Build output $(CWD)/dist"

##########################################
#
# Targets related to example apps
#
##########################################
examples:
	@echo "Run every single example app under examples/"
	@set -e; \
	find $(EXAMPLES_DIR) -name 'run_*.py' | while read -r script; do \
        echo "\nRunning $$script"; \
        $(PYTHON) $$script; \
	done
	@echo "\nExample apps completed"


##########################################
#
# Targets related to unit tests
#
##########################################
test: review unittests

unittests:
	@echo "Starting unit tests"
	@pytest tests_without_config
	@pytest --cov=psengine --cov-report html --cov-branch --cov-report term --random-order-bucket=module
	@coverage html


##########################################
#
# Targets related to code review
#
##########################################
review: imports_check format_check syntax_check banner_check typo
rev: imports_check format syntaxfix banner

format:
	@$(FORMAT) $(FOLDERS)

format_check:
	@$(FORMAT) $(FOLDERS) --check

syntax_check:
	@$(CHECK) $(FOLDERS) --ignore FIX

syntaxfix:
	@$(CHECK) $(FOLDERS) --fix

imports_check:
	@output=$$(find ./psengine -type f -name '*.py' -exec grep -nE '^from psengine' {} +); \
	if [ -n "$$output" ]; then \
		echo "$$output" | awk -F':' '{print "Filename: " $$1 " Line: " $$2 " Import: " $$3}'; \
		exit 1; \
	else \
		echo "No problematic imports found."; \
	fi

banner_check:
	@error=0; \
	echo "Banner: Checking files."; \
	find psengine psengine_cli -type f -name "*.py" | while IFS= read -r file; do \
		if ! grep -q $(BANNER_PATTERN) "$$file"; then \
			echo "Banner not found in $$file"; \
			error=$$(($$error+1)); \
		fi; \
		if sed -n '1p' "$$file" | grep '"""'; then \
			echo "Banner starts with quotes in $$file"; \
			error=$$(($$error+1)); \
		fi; \
	done; \
	if [ $$error -gt 0 ]; then \
		exit 1; \
	fi

define BANNER_TEXT
##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

endef

export BANNER_TEXT

banner:
	@echo "Banner: Checking files."
	@find psengine psengine_cli -type f -name "*.py" | while IFS= read -r file ; do \
		if ! grep -q $(BANNER_PATTERN) "$$file"; then \
			echo "Banner added to $$file"; \
			python3 -c "import os; banner = os.environ['BANNER_TEXT'] + '\n'; fname = '$$file'; f = open(fname, 'r+'); content = f.read(); f.seek(0); f.write(banner + content); f.close()"; \
		fi; \
	done


typo:
	@$(TYPOS) psengine
	@$(TYPOS) psengine_cli
	@$(TYPOS) README.rst CHANGELOG.rst

##########################################
#
# Misc targets
#
##########################################
clean:
	@echo "Removing build and packaging artifacts"
	@rm -rf build

clear_cache:
	@echo "Clearing python cache"
	@find ./psengine ./psengine_cli ./tests -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .coverage
