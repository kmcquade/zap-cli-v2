.PHONY: test coverage setup-env setup-dev test build install clean

SHELL=/bin/bash

coverage:
	rm -f .coverage*
	coverage run --source=zapcli -m pytest -x tests
	coverage report

setup-env:
	python3 -m venv ./venv && source venv/bin/activate
	python3 -m pip install -r requirements.txt

setup-dev: setup-env
	python3 -m pip install -r requirements-dev.txt

test:
	python3 -m coverage run -m pytest -v

build: setup-env clean
	python3 -m pip install --upgrade setuptools wheel
	python3 -m setup -q sdist bdist_wheel

install: build
	python3 -m pip install -q ./dist/zap-cli-v2*.tar.gz
	zap-cli-v2 --help

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '*.egg-link' -delete
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
