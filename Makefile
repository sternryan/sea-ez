.PHONY: test report gates
test:
	.venv/bin/pytest tests/ -v
report:
	.venv/bin/python scripts/margin_report.py
gates:
	.venv/bin/pytest tests/ -q
	.venv/bin/python scripts/design_report.py
