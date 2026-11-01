PYTHON ?= python

.PHONY: setup data build backtest forecast figures lint test all

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

figures:
	$(PYTHON) -m metrocouncils.figures

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest

all: data build backtest forecast figures test
