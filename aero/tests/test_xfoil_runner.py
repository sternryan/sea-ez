from pathlib import Path

import pytest

from aero.xfoil_runner import clmax, run_polar


def test_naca4412_polar_re1m(tmp_path):
    pts = run_polar("NACA 4412", reynolds=1.06e6,
                    alpha_start=0.0, alpha_end=18.0, alpha_step=1.0,
                    workdir=tmp_path)
    assert len(pts) >= 12                      # most points converge
    cl, a = clmax(pts)
    assert 1.55 <= cl <= 1.80                  # spike run: 1.665 @ 16 deg, Re 1.2e6
    assert 13.0 <= a <= 18.0
    # drag sanity at low alpha
    low = [p for p in pts if p.alpha_deg <= 4.0]
    assert all(0.004 <= p.cd <= 0.02 for p in low)
