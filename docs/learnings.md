# Learnings

### FAA/Legiscite claims: fetch the primary PDF, WebFetch gets 403'd
<!-- problem_type: workflow -->
<!-- component: research memos -->
<!-- root_cause: faa.gov blocks default fetchers; search snippets paraphrase regulatory text -->
<!-- resolution_type: workaround -->
<!-- severity: high -->
<!-- date: 2026-07-28 -->

**Problem:** Load-bearing regulatory claims (AC 103-7 weight allowances) needed verbatim verification; faa.gov 403s WebFetch.
**Root Cause:** FAA blocks non-browser user agents; secondary sources paraphrase.
**Solution:** `curl -A "<browser UA>"` + `pdftotext -layout`, read the raw text; reviewer reproduced the same method independently and confirmed verbatim.
**Key Insight:** For life-safety/legal claims, the bar is "two agents independently extracted the same primary text" — search-snippet sourcing would have missed that AC 103-7 ¶18.a.(2)(ii) explicitly names the amphibious-fuselage case.

### Spec numbers written from model memory are hypotheses — mandatory-source memos catch them
<!-- problem_type: workflow -->
<!-- component: design spec -->
<!-- root_cause: spec cited "Kolb Firefly ≈130 sq ft" from recall; published figure is 117 -->
<!-- resolution_type: fix -->
<!-- severity: medium -->
<!-- date: 2026-07-28 -->

**Problem:** The design spec carried a wrong donor datum (Firefly wing area ≈130 sq ft vs sourced 117) that would have seeded Phase 2 CAD scaling math.
**Root Cause:** Datum written during brainstorming from model memory, unverified.
**Solution:** The donor-research memo's "every number carries a URL or unverified tag" rule surfaced the conflict; spec corrected (commit 727d978) same session.
**Key Insight:** Research-memo tasks with a hard citation rule double as spec linters — the discrepancy was found because the memo was FORBIDDEN from restating spec numbers as facts.

### Mixed z-datums silently made two physics gates anti-conservative
<!-- problem_type: bug -->
<!-- component: seaez/hydro.py, seaez/roadmode.py -->
<!-- root_cause: three coexisting vertical datums (keel-baseline params frame, mesh z frame with keel at ~0.2 ft, ground plane below keel) mixed inside gate formulas -->
<!-- resolution_type: fix -->
<!-- severity: high -->
<!-- date: 2026-07-29 -->

**Problem:** Sponson-touch heel and road-tipover gates passed with wrong numbers (4.3° vs 5.0°, 0.72 g vs 0.58 g) — both errors in the anti-conservative direction on a life-safety project.
**Root Cause:** `wing_z_ft` (keel datum) subtracted a mesh-datum waterline; tipover treated CG-above-keel as CG-above-ground. Per-task reviews all approved; only the adversarial whole-branch review caught it by recomputing in a consistent frame.
**Solution:** Renamed args to carry the datum (`waterline_above_keel_ft`), added `keel_to_ground_ft` param, converted at call sites via `wl - mesh.bounds[0][2]`.
**Key Insight:** In geometry-backed gate code, put the datum IN the parameter name and convert at the boundary — and note that plausible-looking margins hide datum bugs, so the final reviewer must re-derive at least one number per gate in a single consistent frame.

### Well-spec'd plans make cheap-model SDD nearly frictionless
<!-- problem_type: workflow -->
<!-- component: SDD loop / plan authoring -->
<!-- root_cause: plan contained complete code + expected numeric outcomes per task, so implementers were transcribers and reviewers were verifiers -->
<!-- resolution_type: design_change -->
<!-- severity: medium -->
<!-- date: 2026-07-29 -->

**Problem:** 10-task phase risked burning session budget on frontier-model implementers.
**Root Cause:** N/A — this is a positive pattern capture.
**Solution:** Fable wrote the plan with exact code, exact YAML tables, and hand-calculated expected values (479 lb, 31.8% MAC, ~0.72 ratio); haiku transcribed pure-code tasks, sonnet handled multi-file/CAD tasks; every implementer's computed numbers matched the plan's predictions, so drift was instantly visible.
**Key Insight:** Hand-computing expected gate values INTO the plan turns every subagent report into a self-checking oracle — mismatch = bug, match = cheap confidence. Worth the planning time on any physics/numeric pipeline.

### Second stale-assumption catch: a "constant" that survived a redesign
<!-- problem_type: architecture -->
<!-- component: seaez/params.py tail_ac_x_ft -->
<!-- root_cause: 17.4 was the OLD stab's geometric center; the tail was resized around it and the label quietly became a lie -->
<!-- resolution_type: design_change -->
<!-- severity: medium -->
<!-- date: 2026-07-29 -->

**Problem:** V_h gate passed on a station labeled "tail AC" that was actually the superseded massing tail's geometric center; two of the four analytic stability gates had thinner true margins than the ambiguity.
**Root Cause:** Resizing one parameter (stab area) without re-deriving the stations that depended on the old geometry. Per-task reviewers verified formulas against the brief; only the whole-branch adversarial pass re-derived the station from the massing source.
**Solution:** Boom extension (overall 18.5→19.4 ft) makes 17.4 an honest quarter-chord AC; new consistency test pins stab TE ≤ overall length; hardcoded duplicate of overall length removed from foldmode.
**Key Insight:** When a design parameter changes, grep for every station/constant derived from the OLD value — and add a geometric-consistency test (part fits inside declared envelope) so the class of bug can't recur silently. Final reviews should re-derive stations from primary geometry, not just check formulas.

## Phase 2.3a (2026-07-29) — computed-aero grounding

- **Parm round-trip ≠ built geometry.** OpenVSP POD FineRatio is Length/RADIUS (built hull 2x wide, crossed the keel datum) and the brief's Sweep=0 wing violated the chords-centered convention (AC at 14.5% MAC, −10 pts of phantom instability). Both slipped past parm-echo checks; both were caught only by measuring the BUILT surface (absolute-frame bbox, CompPnt01 probes). Guard class: every CAD-model test must measure built geometry in the absolute frame.
- **Guards can fail open.** The staleness fingerprint's `float(fp.get(k, nan)) - cur > tol` was always False for MISSING keys — a fail-closed guard silently inverted. NaN never survives a comparison; never use get()-with-NaN-default in a validator.
- **Convention seams between analytic SSOT and CAD are the recurring bug class** (2.1 datum mixing, 2.2 stale station, 2.3a chords-centered). The wing-alone VLM anchor (untapered wing must show NP≈25% MAC) is the cheap canary that caught it this time — keep pipeline anchors in every solver integration.
- **Fixed-width Fortran buffers truncate long paths silently** (XFOIL PACC and LOAD) — short relative names + cwd, always.
- Honest outcome: usa35b selected (2D 1.694 → 3D 1.5246), stall 25.75 kt > 24 ceiling; VSPAERO SM +5.46% < 8% target (α-dependent, ≈+2.2% at α=−2°); CNβ +0.0412 green. Both shortfalls surfaced to Ryan in docs/research/2026-07-29-airfoil-clmax-finding.md rather than gate-fudged.
