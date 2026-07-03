.PHONY: check clean coverage format format-check lint lint-complexity test validate validate-config validate-likec4 validate-structurizr

PYTHON ?= python
KMAP ?= kmap
COMPLEXITY_RULES := C901
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0124
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0133
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0202
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0203
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0206
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0402
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0904
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0911
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0912
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0913
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0914
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0915
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0916
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR0917
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1702
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1704
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1708
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1711
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1712
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1714
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1716
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1722
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1730
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1733
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR1736
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR2004
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR2044
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR5501
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR6104
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR6201
COMPLEXITY_RULES := $(COMPLEXITY_RULES),PLR6301

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

lint-complexity:
	$(PYTHON) -m ruff check --preview --select $(COMPLEXITY_RULES) .

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html

validate-config:
	@set -eu; \
	for config in config/*.yaml; do \
		echo "Validating kmap config: $$config"; \
		$(KMAP) validate-config "$$config"; \
	done

validate-likec4:
	$(KMAP) validate-likec4 --root Likec4

validate-structurizr:
	$(KMAP) validate-structurizr --root Structurizr

validate: validate-likec4 validate-structurizr

check: lint format-check lint-complexity coverage validate

clean:
	find kmap tests -type d -name __pycache__ -prune -exec rm -r {} +
	rm -rf .tmp/pytest_cache .tmp/ruff_cache .tmp/htmlcov .tmp/.coverage .tmp/coverage.xml dist build *.egg-info
