# PY defaults to the repo-local venv but is overridable, so a fresh clone runs in
# whatever environment the caller already has:  make gates PY=python
PY ?= .venv/bin/python

.PHONY: test report gates tools aero aero-test
test:
	$(PY) -m pytest tests/ -v
report:
	$(PY) scripts/margin_report.py
gates:
	$(PY) -m pytest tests/ -q
	$(PY) scripts/design_report.py
tools:
	bash scripts/install_aero_tools.sh
aero:
	tools/venv313/bin/python -m aero.airfoil_select
	tools/venv313/bin/python -m aero.vsp_stability
aero-test:
	tools/venv313/bin/python -m pytest aero/tests -q
