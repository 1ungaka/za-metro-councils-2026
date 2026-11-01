PYTHON ?= python

.PHONY: setup data build backtest forecast figures dashboard lint test all

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

dashboard:
	$(PYTHON) -m metrocouncils.dashboard

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest

all: data build backtest forecast figures dashboard test
