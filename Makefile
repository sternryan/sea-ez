.PHONY: test report gates tools aero aero-test
test:
	.venv/bin/pytest tests/ -v
report:
	.venv/bin/python scripts/margin_report.py
gates:
	.venv/bin/pytest tests/ -q
	.venv/bin/python scripts/design_report.py
tools:
	bash scripts/install_aero_tools.sh
aero:
	tools/venv313/bin/python -m aero.airfoil_select
	tools/venv313/bin/python -m aero.vsp_stability
aero-test:
	tools/venv313/bin/python -m pytest aero/tests -q
