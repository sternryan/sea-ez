import math
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


def _naca4_selig_coords(m: float, p: float, t: float, n: int = 30) -> str:
    """Hand-rolled NACA 4-digit coordinate generator (Selig format: TE->LE
    over the top, then LE->TE along the bottom). Self-contained so the LOAD
    test below doesn't depend on a committed .dat file (Task 4 adds one)."""
    def thickness(x: float) -> float:
        return 5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2
                        + 0.2843 * x**3 - 0.1015 * x**4)

    def camber(x: float) -> tuple[float, float]:
        if x < p:
            yc = m / p**2 * (2 * p * x - x**2)
            dyc = 2 * m / p**2 * (p - x)
        else:
            yc = m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * x - x**2)
            dyc = 2 * m / (1 - p)**2 * (p - x)
        return yc, dyc

    xs = [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    upper, lower = [], []
    for x in xs:
        yc, dyc = camber(x)
        theta = math.atan(dyc)
        yt = thickness(x)
        upper.append((x - yt * math.sin(theta), yc + yt * math.cos(theta)))
        lower.append((x + yt * math.sin(theta), yc - yt * math.cos(theta)))
    pts = list(reversed(upper)) + lower[1:]
    lines = ["Test NACA 4412 approx"] + [f"{x:.6f}  {y:.6f}" for x, y in pts]
    return "\n".join(lines) + "\n"


def test_load_dat_file_deep_tmp_path(tmp_path):
    # Regression test: XFOIL's LOAD command reads a filename into a
    # fixed-width Fortran buffer that silently truncates long absolute
    # paths (same bug class as PACC). pytest's tmp_path is already long;
    # nest further to make sure a real-world deep workdir stays covered.
    source_dir = tmp_path / "deeply" / "nested" / "location" / "for" / "airfoil" / "source"
    source_dir.mkdir(parents=True)
    dat_path = source_dir / "test_airfoil_selig_format_coordinates.dat"
    dat_path.write_text(_naca4_selig_coords(0.04, 0.4, 0.12))

    workdir = tmp_path / "work"
    workdir.mkdir()

    pts = run_polar(dat_path, reynolds=1.06e6,
                    alpha_start=0.0, alpha_end=4.0, alpha_step=2.0,
                    workdir=workdir)
    assert len(pts) >= 1
    assert all(0.0 <= p.alpha_deg <= 4.0 for p in pts)
    assert all(p.cl > 0.2 for p in pts)          # cambered section lifts at low alpha
