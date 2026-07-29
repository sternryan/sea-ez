"""Run VSPAERO (VLM, stability mode) on the DesignParams model and write
data/aero/vspaero_stability.json. NP from -CMa/CLa about the CG.

Design-consistency tooling — NOT validated engineering.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import openvsp as vsp

from aero.fingerprint import params_fingerprint
from aero.vsp_model import build_model
from seaez.params import DEFAULT
from seaez.sizing import FPS_PER_KT, planform, stall_speed_kt

ROOT = Path(__file__).parent.parent

# VLM SM sanity band. The brief's original 3-25% MAC band assumed the VLM
# result would land lower than the analytic oracle (SM 11.5%) but still
# stable. A 2026-07-29 diagnostic session (4 experiments, recorded in
# DIAGNOSTICS below and in task-6-report.md) found the real VLM result is
# -3.5% MAC (mildly unstable) and traced it to genuine aerodynamics, not a
# script/reference bug: an alpha sweep, a tail-height perturbation, a
# wake-convergence check, a panel-vs-VLM cross-check, and an untapered-wing
# sanity anchor all confirm this. Per team-lead direction (2026-07-29), the
# gate here now only screens for gross numerical/reference garbage; whether
# -3.5% SM is acceptable for the design is a Task 8 Ryan-checkpoint call,
# not this script's.
SM_MIN_FRAC, SM_MAX_FRAC = -0.20, 0.30
CNB_MIN_PER_RAD, CNB_MAX_PER_RAD = -0.02, 0.08

# Recorded findings from the 2026-07-29 diagnostic session (not recomputed
# on every run -- these are a point-in-time investigation of *why* SM comes
# out negative, committed alongside the primary result for the Task 8
# checkpoint). See task-6-report.md for full methodology and raw output.
DIAGNOSTICS = {
    "alpha_sweep_cma_per_rad_no_hull": {
        "-2": 0.2290, "0": 0.1416, "2": 0.0516, "4": -0.0406, "6": -0.1506,
    },
    "alpha_sweep_note": (
        "Smooth, monotonic, converged trend (not solver noise) -- consistent "
        "with the wing wake sheet's position relative to the fixed-height "
        "stab shifting with base alpha, not a numerical artifact."
    ),
    "wake_convergence_sm_frac_mac_full_model_alpha2": {
        "wake_iters_5_default": -0.0351, "wake_iters_15": -0.0339, "wake_iters_30": -0.0339,
    },
    "wake_convergence_note": "Converged to <0.2 MAC points; not under-resolved.",
    "tail_height_plus_1_5ft_no_hull_alpha2": {
        "cma_baseline": 0.0516, "cma_stab_raised_1_5ft": 0.0929,
        "sm_baseline_frac_mac": -0.0097, "sm_stab_raised_1_5ft_frac_mac": -0.0176,
    },
    "tail_height_note": (
        "Raising the stab 1.5 ft (toward the wing's Z) made CMa MORE "
        "destabilizing, not less -- opposite the a-priori guess, but it "
        "proves strong sensitivity to tail height (i.e. wake proximity, not "
        "a reference bug, drives the result); the wake sheet likely sits "
        "near/at the wing's height band at this alpha."
    ),
    "panel_vs_vlm_sm_frac_mac_no_hull_alpha2": {"vlm": -0.0097, "panel": -0.0040},
    "panel_vs_vlm_note": (
        "Two independent solution methods agree to within 0.6 MAC points -- "
        "not a VLM-specific implementation artifact."
    ),
    "wing_alone_np_frac_mac_anchor": {"taper_1_0_untapered": 0.2407, "taper_0_65_actual": 0.1454},
    "wing_alone_note": (
        "Untapered wing lands at 24.1% MAC, matching the textbook "
        "quarter-chord AC (~25%) and confirming the MAC/reference pipeline "
        "is correct. The actual params wing (taper 0.65, zero LE sweep) "
        "lands at 14.5% -- a real ~10-point forward AC shift from taper "
        "with an unswept LE (the c/4 line sweeps forward going outboard), "
        "not a bug."
    ),
    "verdict": (
        "SM=-3.5% MAC at the rotation-AoA condition is real, not a script or "
        "reference artifact. It compounds three genuine effects: (1) taper "
        "0.65 with zero LE sweep shifts the isolated wing's own AC ~10 MAC "
        "points forward of the quarter-MAC assumption seaez/sizing.py's "
        "V_h/V_v hand calc relies on; (2) the stab loses real effectiveness "
        "to wing-wake proximity at this alpha (confirmed by cross-solver "
        "agreement and height sensitivity); (3) the hull fuselage adds ~2.5 "
        "further MAC points of destabilization. seaez/sizing.py has no "
        "downwash term and assumes AC=quarter-MAC, so its +11.5% SM oracle "
        "is optimistic for this short-coupled, low-tail layout."
    ),
}


def main() -> None:
    p = DEFAULT
    fp = params_fingerprint()
    pf = planform(p.wing_area_sqft, p.wing_span_ft, p.wing_taper_ratio, p.wing_center_x_ft)
    vs = stall_speed_kt(fp["gross_lb"], p.wing_area_sqft, p.cl_max)
    vinf_kt = 1.2 * vs  # rotation-speed condition, matches the analytic gates

    # VSPAERO writes a pile of scratch files (.history/.lod/.stab/.vspgeom/...)
    # next to the .vsp3 it analyzes -- build/run in a scratch dir so only
    # the committed .vsp3 + JSON land in data/aero/, and only once we know
    # the run is worth keeping (nothing committed on a hard-fail).
    scratch_dir = Path(tempfile.mkdtemp(prefix="seaez_vspaero_"))
    scratch_vsp3 = scratch_dir / "seaez_noforeplane.vsp3"
    build_model(save_path=scratch_vsp3)

    # VSPAEROSweep has no "AnalysisMethod" input in this OpenVSP build (3.51.2) --
    # VLM vs. panel is selected by which Set a component's membership feeds
    # ("GeomSet" = panel/thick, "ThinGeomSet" = VLM/thin). All 4 components
    # (wing/stab/fin/hull) go into ThinGeomSet=SET_ALL so the fuselage is
    # represented as a slender thin-body in the VLM solve; GeomSet=SET_NONE
    # so no panel meshing (and its scratch .tri/.history files) is attempted.
    geom_an = "VSPAEROComputeGeometry"
    vsp.SetAnalysisInputDefaults(geom_an)
    vsp.SetIntAnalysisInput(geom_an, "GeomSet", [vsp.SET_NONE])
    vsp.SetIntAnalysisInput(geom_an, "ThinGeomSet", [vsp.SET_ALL])
    vsp.ExecAnalysis(geom_an)

    an = "VSPAEROSweep"
    vsp.SetAnalysisInputDefaults(an)
    vsp.SetIntAnalysisInput(an, "GeomSet", [vsp.SET_NONE])
    vsp.SetIntAnalysisInput(an, "ThinGeomSet", [vsp.SET_ALL])
    vsp.SetIntAnalysisInput(an, "UnsteadyType", [vsp.STABILITY_DEFAULT])
    vsp.SetDoubleAnalysisInput(an, "Sref", [p.wing_area_sqft])
    vsp.SetDoubleAnalysisInput(an, "bref", [p.wing_span_ft])
    vsp.SetDoubleAnalysisInput(an, "cref", [pf.mac_ft])
    vsp.SetIntAnalysisInput(an, "RefFlag", [vsp.MANUAL_REF])
    vsp.SetDoubleAnalysisInput(an, "Xcg", [fp["cg_x_ft"]])
    vsp.SetDoubleAnalysisInput(an, "Zcg", [fp["cg_z_ft"]])
    vsp.SetDoubleAnalysisInput(an, "Vinf", [vinf_kt * FPS_PER_KT])
    vsp.SetDoubleAnalysisInput(an, "AlphaStart", [2.0])
    vsp.SetIntAnalysisInput(an, "AlphaNpts", [1])
    vsp.SetIntAnalysisInput(an, "MachNpts", [1])
    vsp.SetDoubleAnalysisInput(an, "MachStart", [0.0])
    vsp.ExecAnalysis(an)

    # Stability derivatives land on the "VSPAERO_Stab" result set. Derivative
    # data names are body-axis (l=roll, m=pitch, n=yaw): CL_Alpha, CMm_Alpha,
    # CMn_Beta. All *_Alpha/*_Beta derivatives here are per RADIAN (confirmed
    # by magnitude: CL_Alpha ~5.3/rad matches AR~8.3 lifting-line theory
    # 2*pi/(1+2/AR)=5.06/rad -- a per-degree value would read ~0.08-0.09).
    sid = vsp.FindLatestResultsID("VSPAERO_Stab")

    def d(name: str) -> float:
        return vsp.GetDoubleResults(sid, name)[0]

    cla, cma = d("CL_Alpha"), d("CMm_Alpha")
    cnb = d("CMn_Beta")
    cg_frac = (fp["cg_x_ft"] - pf.mac_le_x_ft) / pf.mac_ft
    sm = -cma / cla
    np_frac = cg_frac + sm

    # Cross-check against VSPAERO's own SM/X_np (independent internal calc):
    # both must agree with our -CMa/CLa derivation to well within rounding.
    vsp_sm = d("SM")
    vsp_np_frac = (d("X_np") - pf.mac_le_x_ft) / pf.mac_ft
    assert abs(sm - vsp_sm) < 0.01, f"SM mismatch: derived {sm} vs VSPAERO's own {vsp_sm}"
    assert abs(np_frac - vsp_np_frac) < 0.01, (
        f"NP mismatch: derived {np_frac} vs VSPAERO's own {vsp_np_frac}"
    )

    if not (SM_MIN_FRAC <= sm <= SM_MAX_FRAC):
        raise RuntimeError(
            f"Static margin {sm:.1%} MAC (NP {np_frac:.1%}, CG {cg_frac:.1%}) is "
            f"outside the numerical-sanity {SM_MIN_FRAC:.0%}-{SM_MAX_FRAC:.0%} MAC "
            f"band (analytic oracle: NP 43.3%, SM 11.5%). CLa={cla:.4f}/rad "
            f"CMa={cma:.4f}/rad -- reference quantities (Sref={p.wing_area_sqft}, "
            f"bref={p.wing_span_ft}, cref={pf.mac_ft:.4f}, "
            f"Xcg={fp['cg_x_ft']}) match params/fingerprint, so this would reflect "
            f"a real (if extreme) VLM result rather than a wiring bug -- but it's "
            f"well past even the diagnosed -3.5% finding, so treat as suspect and "
            f"re-run the 2026-07-29 diagnostic session before accepting."
        )
    if not (CNB_MIN_PER_RAD <= cnb <= CNB_MAX_PER_RAD):
        raise RuntimeError(
            f"CNb {cnb:+.4f}/rad is outside the sane "
            f"{CNB_MIN_PER_RAD:+.2f}..{CNB_MAX_PER_RAD:+.2f}/rad band."
        )

    out = {
        "fingerprint": fp,
        "reference": {"sref_sqft": p.wing_area_sqft, "bref_ft": p.wing_span_ft,
                       "cref_ft": round(pf.mac_ft, 4), "xcg_ft": fp["cg_x_ft"],
                       "zcg_ft": fp["cg_z_ft"], "vinf_kt": round(vinf_kt, 2)},
        "derivatives": {"CMa_per_rad": round(cma, 4), "CLa_per_rad": round(cla, 4),
                         "CNb_per_rad": round(cnb, 4),
                         "neutral_point_frac_mac": round(np_frac, 4)},
        "static_margin_frac_mac": round(sm, 4),
        "diagnostics": DIAGNOSTICS,
    }
    dest_dir = ROOT / "data" / "aero"
    dest = dest_dir / "vspaero_stability.json"
    dest.write_text(json.dumps(out, indent=1))
    (dest_dir / "seaez_noforeplane.vsp3").write_bytes(scratch_vsp3.read_bytes())
    print(f"SM {sm:.1%} MAC, NP {np_frac:.1%} MAC, CNb {cnb:+.4f}/rad -> {dest}")


if __name__ == "__main__":
    main()
