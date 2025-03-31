# The only place to bump the version
VERSION := 0.0.1
VERSION_FILE := {{ cookiecutter.lib_folder_name }}/_version.py
BUILDID := $(if $(SVN_REVISION),$(SVN_REVISION),$(shell git rev-list --count HEAD))
PCK_DIR := {{ cookiecutter.project_name }}_$(VERSION)-$(BUILDID)
PACKAGE := $(PCK_DIR).tar.gz
BUILD_DIR := pkg_build
BUILD_OUT := $(BUILD_DIR)/$(PCK_DIR)

# Commands
PYTHON := python3.10
RUN_PYTEST := $(PYTHON) -m pytest
FORMAT := ruff format
CHECK := ruff check 
CWD := $(shell pwd)
VIRTUALENV := $(shell command -v virtualenv 2> /dev/null)
UNAME := $(shell uname)
RSYNC := rsync -rav
TAR := tar
MV := mv

# MacOSX & Unix support
SED := sed
ifeq ($(UNAME),Darwin)
SED:= sed -i ''
else
SED:= sed -i
endif

.PHONY: all, unittests, clear_cache, review, format, review, rev, syntaxfix, test, clean, setup

help:
	@echo "Available targets:" 
	@echo " setup       - Setup dev environment (install venv, dependencies)"
	@echo " test        - run review and unittests"
	@echo " unittests   - run unittests"
	@echo " review      - run black_check, flake8, pylint and pydocstyle"
	@echo " format      - run ruff format"
	@echo " syntaxfix   - run ruff check --fix"
	@echo " rev		    - run ruff check --fix and ruff format"
	@echo " review      - run ruff check and ruff format"
	@echo " build       - prepares the files for packaging"
	@echo " package     - run build & prepare the tar.gz file"
	@echo " pdf         - export install guide PDF from a Confluence page"
	@echo "Miscellaneous targets:"
	@echo " clean       - delete build and packaging artifacts"
	@echo " clear_cache - remove python cache & useless dirs"

##########################################
#
# Targets related to versioning:
#  - {{ cookiecutter.lib_folder_name }}/_version.py
#
##########################################
versionBump:
	@echo "Bumping version to $(VERSION)"
	@ $(SED) '/__version__ = / s/__version__ = [^,]*/__version__ = "$(VERSION)"/' $(VERSION_FILE)
	@make format

##########################################
#
# Targets related to build
#
##########################################
build: versionBump format clear_cache build_dirs build_rsync


build_dirs:
	@echo "* Creating build root directory"
	mkdir -p $(BUILD_DIR)
	@if [ -d $(BUILD_OUT) ]; then rm -rf $(BUILD_OUT); fi
	@echo "* Creating build output directory $(BUILD_OUT)"
	mkdir -p $(BUILD_OUT)
	# mkdir -p $(BUILD_OUT)/deps

build_rsync: build_dirs
	@echo "* Copying files to build output directory"
	$(RSYNC) {{ cookiecutter.lib_folder_name }} $(BUILD_OUT) --exclude='*.pyc'
	$(RSYNC) config $(BUILD_OUT) --exclude='*.pyc'
	$(RSYNC) {{cookiecutter.run_file_name }}.py $(BUILD_OUT)
	$(RSYNC) requirements.txt $(BUILD_OUT)
	$(RSYNC) README.rst $(BUILD_OUT)
	# $(RSYNC) deps/psengine-*.whl $(BUILD_OUT)/deps
	

##########################################
#
# Targets related to package
#
##########################################
package: build package_gzip calculate_sha256sum


package_gzip:
	@echo "* Packaging $(PACKAGE)"
	$(TAR) -zcv --exclude='.DS_Store' --exclude "__MACOSX" --exclude "__pycache__" -C $(BUILD_DIR) -f $(PACKAGE) $(PCK_DIR)
	@echo "* Removing build artifacts"
	rm -rf $(BUILD_OUT)/*
	@echo "* Moving package to build output directory"
	$(MV) $(PACKAGE) $(BUILD_OUT)
	@echo "* Packaging has completed successfully"
	@echo "* Package is ready for client delivery: $(BUILD_OUT)/$(PACKAGE)"

calculate_sha256sum:
	@echo "* Calculating sha256sum for $(PACKAGE)"
	shasum -a 256 $(BUILD_OUT)/$(PACKAGE) | awk '{print $$1}' > $(BUILD_OUT)/$(PACKAGE).sha256sum

##########################################
#
# Targets related to development environment setup
#
##########################################
setup:
    ifndef VIRTUALENV
		@echo "virtualenv not found, using python3 -m venv venv"
		$(PYTHON) -m venv venv
    else
		@echo "Creating virtual environment using virtualenv"
		virtualenv venv
    endif
	
	. $(CWD)/venv/bin/activate && pip install -r requirements_dev.txt
	@echo "Success! Development environment is ready"
	@echo "Please activate the virtualenv with: source venv/bin/activate"

##########################################
#
# Targets related to unittest
#
##########################################
test: review unittests

unittests:
	@echo "* Starting unit tests"
	$(RUN_PYTEST) --cov={{ cookiecutter.lib_folder_name }} --cov-report html --cov-branch --cov-report term

##########################################
#
# Targets related to code review
#
##########################################
review: format_check syntax
rev: format syntaxfix

FOLDERS={{ cookiecutter.lib_folder_name }} tests

format:
	@$(FORMAT) $(FOLDERS)

format_check:
	@$(FORMAT) $(FOLDERS) --check

syntax:
	@$(CHECK) $(FOLDERS)

syntaxfix:
	@$(CHECK) $(FOLDERS) --fix

##########################################
#
# Misc targets
#
##########################################
clear_cache:
	@echo "* Removing python cache & useless dirs"
	@@find ./{{ cookiecutter.lib_folder_name }} -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
	@rm -rf .pytest_cache
	@rm -rf __pycache__
