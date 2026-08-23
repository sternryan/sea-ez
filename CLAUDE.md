# sea-ez — a FAR Part 103 amphibious ultralight designed as code, with every limit held by a test

See `README.md` for the current gate table, the run instructions, and what each subsystem
does. `seaez/params.py` is the single source of truth for every airframe parameter.

## Commands

```bash
.venv/bin/pip install -e ".[dev,cad]"   # the `cad` extra is required, not optional
make gates                              # the suite + the margin report — the real check
make test                               # verbose pytest only
make report
make tools                              # install the XFOIL / OpenVSP toolchain
make aero                               # airfoil select + VSPAERO stability, separate interpreter
make aero-test
```

`PY` is overridable (`make gates PY=python`) and defaults to `.venv/bin/python`.

## Conventions

- **Change a parameter, rerun the gates, read what breaks.** Limits live in `tests/`, not in
  a spreadsheet or a comment. A limit nobody enforces is not a limit.
- **Nothing has been built and nothing has flown.** Every number is a target held under an
  automated gate, not validated engineering. The report header says so deliberately — never
  restate a gate value as a measured or verified result.

## Gotchas

- **The `aero/` lane runs on a different interpreter.** `make aero` and `make aero-test` use
  `tools/venv313/bin/python`, not `.venv`. XFOIL and OpenVSP/VSPAERO need it. Running the
  aero modules from the main venv fails in a way that looks like a missing dependency.
- **⚠ Check your datum on every new gate.** Two gates were silently anti-conservative for
  about a week because the massing frame used a bow-x/keel-z datum and the mesh used its own,
  about 0.2 ft apart. Both gates passed the entire time. **Treat a gate that has never failed
  as unproven, not as safe** — this is the repo's most expensive lesson.
- **Three gates have almost no room and drive everything downstream:** static margin sits at
  exactly the 8% floor under VSPAERO with zero margin, computed stall is 23.73 kt against a
  hard regulatory 24, and empty weight has ~17 lb under the Part 103 ceiling. Any parameter
  change touching wing area, weight, or tail geometry will move at least one of them.
- **The analytic and VSPAERO static margins are cross-checked, and their disagreement is
  itself a gate.** Don't "fix" one to match the other; a widening gap is the signal.
- Hull-alone GM is **negative by design** — the sponsons carry roll. It is reported, not
  gated. Do not add a gate that forces it positive.
- `data/aero/*.json` are generated artifacts. When geometry changes, regenerate them; a stale
  polar silently feeds an old CLmax into a gate that then passes.
- Regulatory numbers in `docs/research/` were verified verbatim against the FAA PDFs, not
  from forum posts. Keep that standard — the AC 103-7 amphibious fuselage allowance is
  load-bearing for the weight gate.

## Where things live

- `seaez/params.py` — DesignParams, the SSOT. `seaez/ledger.py` — mass limits.
- `design/geometry.py` — parametric hull as a watertight mesh; the hydrostatic gates measure
  it directly rather than trusting a hand-entered displacement.
- `aero/` — XFOIL + OpenVSP/VSPAERO, feeding computed CLmax and stability derivatives back.
- `data/parts.yaml` — per-part mass and x/z stations feeding the CG rollup.
- `docs/research/` — sourced regulatory memos.
