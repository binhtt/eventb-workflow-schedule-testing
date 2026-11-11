PYTHON ?= python3

.PHONY: audit test smoke full analysis

audit:
	$(PYTHON) scripts/verify_artifact.py

test: audit
	$(PYTHON) -m unittest discover -v -s code -p checks.py

smoke:
	$(PYTHON) code/reproduce.py --mode smoke

full:
	$(PYTHON) code/reproduce.py --mode full

analysis:
	$(PYTHON) code/reproduce.py --mode analysis

.PHONY: supplemental supplemental-audit

supplemental:
	$(PYTHON) scripts/supplemental/ablation_review.py
	$(PYTHON) scripts/supplemental/dfs_review.py
	$(PYTHON) scripts/supplemental/time_review.py
	$(PYTHON) scripts/supplemental/verify_review.py --generated outputs/supplemental
	$(PYTHON) scripts/supplemental/summary_review.py

supplemental-audit:
	$(PYTHON) scripts/supplemental/verify_review.py
