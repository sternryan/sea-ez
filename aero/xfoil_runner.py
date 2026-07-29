"""Batch XFOIL driver (aero lane, tools/venv313 + source-built xfoil 6.97).

Design-consistency tooling on targets — NOT validated engineering and NOT
airworthiness proof (spec safety notice). 2D section polars only; 3D wing
decrement is applied downstream in seaez/aerodata.py.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

XFOIL_BIN = Path(__file__).parent.parent / "tools" / "xfoil-src" / "build" / "src" / "xfoil"
NCRIT = 9  # standard free-transition e^n default; documented, not tuned


@dataclass(frozen=True)
class PolarPoint:
    alpha_deg: float
    cl: float
    cd: float
    cm: float


def _commands(airfoil: str | Path, reynolds: float, a0: float, a1: float,
              da: float, polar_path: Path) -> str:
    load = f"NACA {airfoil.split()[1]}" if isinstance(airfoil, str) else f"LOAD {airfoil}"
    # PLOP/G first: headless build aborts on ASEQ if graphics are enabled.
    return "\n".join([
        "PLOP", "G", "",
        load,
        "PANE",                      # repanel loaded coordinates (no-op for NACA)
        "OPER",
        f"VISC {reynolds:.6g}",
        "ITER 100",
        "PACC", str(polar_path), "",
        f"ASEQ {a0} {a1} {da}",
        "", "QUIT",
    ]) + "\n"


def _parse_polar(polar_path: Path) -> list[PolarPoint]:
    pts = []
    for line in polar_path.read_text().splitlines():
        f = line.split()
        if len(f) >= 5:
            try:
                pts.append(PolarPoint(float(f[0]), float(f[1]), float(f[2]), float(f[4])))
            except ValueError:
                continue  # header / separator rows
    return sorted(pts, key=lambda p: p.alpha_deg)


def run_polar(airfoil: str | Path, reynolds: float, alpha_start: float,
              alpha_end: float, alpha_step: float, workdir: Path) -> list[PolarPoint]:
    polar = workdir / "polar.txt"
    polar.unlink(missing_ok=True)
    # XFOIL's PACC filename buffer is fixed-width and silently truncates long
    # absolute paths (observed with pytest's tmp_path). Pass a bare relative
    # name instead — subprocess cwd is already set to workdir below.
    cmds = _commands(airfoil, reynolds, alpha_start, alpha_end, alpha_step, Path(polar.name))
    subprocess.run([str(XFOIL_BIN)], input=cmds, capture_output=True,
                   text=True, cwd=workdir, timeout=120)
    if not polar.exists():
        raise RuntimeError(f"XFOIL produced no polar for {airfoil}")
    pts = _parse_polar(polar)
    if not pts:
        raise RuntimeError(f"XFOIL polar empty (no converged points) for {airfoil}")
    return pts


def clmax(points: list[PolarPoint]) -> tuple[float, float]:
    best = max(points, key=lambda p: p.cl)
    return best.cl, best.alpha_deg
