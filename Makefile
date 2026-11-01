PYTHON ?= python

.PHONY: setup data build backtest forecast lint test all

setup:
	$(PYTHON) -m pip install -e ".[dev]"

data:
	$(PYTHON) -m metrocouncils.download

build:
	$(PYTHON) -m metrocouncils.build

backtest:
	$(PYTHON) -m metrocouncils.backtest

forecast:
	$(PYTHON) -m metrocouncils.forecast

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest

all: data build backtest forecast test
