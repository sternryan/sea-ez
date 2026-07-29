.PHONY: test report
test:
	.venv/bin/pytest tests/ -v
report:
	.venv/bin/python scripts/margin_report.py
