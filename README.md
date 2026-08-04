# sea-ez

A FAR Part 103 amphibious ultralight, designed as code. Every airframe decision is a
parameter in one file, and every limit that matters is a test that fails the build.

**Status: design in progress. Nothing has been built and nothing has flown.** The numbers
below are targets held under automated gates, not validated engineering. The report says so
in its own header, and that is deliberate. A limit nobody enforces is not a limit, and a
number nobody labels is a lie waiting to happen.

## The gates

`make gates` runs the suite and prints the current margin report. CI runs the same command
on every push.

```
  empty weight (lb)                         237.0   [<= 254]
  chute (lb)                                 22.0   [<= 24]
  gross w/ pilot+fuel (lb)                  479.0   [470-500]
  stall @ gross, CLmax 1.79 (kt)            23.76   [<= 24]
  gross CG (%MAC)                           33.8%   [25-35%]
  hull volume (ft^3)                         27.4   [>= foam reserve 2x1.5xW]
  static draft (ft)                          0.64   [< 75% depth]
  freeboard @ step (ft)                      1.31   [>= 0.33]
  hull-alone GM (ft)                        -0.76   [report only]
  sponson touch heel (deg)                    5.0   [<= 10]
  road tipover threshold (g)                 0.58   [>= 0.4]
  horiz tail volume V_h                     0.455   [>= 0.35]
  vert tail volume V_v                     0.0160   [>= 0.012]
  static margin (%MAC, analytic)            13.8%   [>= 8%]
  tail/thrust-couple ratio @1.2Vs            1.60   [>= 1.2]
  folded width (ft)                          4.70   [< 5]
  folded length (ft)                         25.7   [report: spec said 18-19]
  airfoil (XFOIL, Re 1066k)                usa35b   [clmax_2d 1.69]
  flaperon dCLmax_2d                        +0.30   [landing config, 2.3b builds it]
  CLmax_3D landing (0.90 x (2D+flap))       1.795   [>= 1.755 for 24 kt]
  stall @ COMPUTED landing CLmax (kt)       23.73   [<= 24]
  static margin (%MAC, VSPAERO)              8.0%   [>= 8%]
  CNbeta (/rad, VSPAERO w/ hull)          +0.0480   [> 0]
  SM cross-check |vsp - analytic|            5.8%   [<= 8%]
```

The tight ones are the interesting ones. Static margin sits at exactly the 8% floor under
VSPAERO with zero margin, stall computes to 23.73 kt against a hard regulatory 24, and empty
weight has 17 lb of headroom against the Part 103 ceiling. Those three drive every subsequent
decision.

## Run it

```bash
git clone https://github.com/sternryan/sea-ez && cd sea-ez
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,cad]"
make gates
```

The `cad` extra is required, not optional: the hydrostatics tests import `trimesh`. `PY` is
overridable if you keep your environment somewhere else, e.g. `make gates PY=python`.

## How it works

- **`seaez/params.py`** is the single source of truth. Change a parameter, rerun the gates,
  see what breaks.
- **`tests/`** encodes the limits. Part 103 empty weight, stall ceiling, CG envelope, tail
  volumes, static margin, hydrostatics, road tipover. A parameter change that violates a
  limit fails the build rather than sitting in a stale spreadsheet.
- **`design/geometry.py`** generates the parametric hull as a watertight mesh, which the
  hydrostatic gates measure directly instead of trusting a hand-entered displacement.
- **`aero/`** runs the XFOIL and OpenVSP/VSPAERO lane on a separate interpreter and feeds
  computed CLmax and stability derivatives back into the gates. Analytic and VSPAERO static
  margin are cross-checked against each other, and the disagreement is itself a gate.
- **`docs/research/`** holds sourced regulatory memos. The AC 103-7 amphibious fuselage
  weight allowance was verified verbatim against the FAA PDF, not taken from a forum post.

## A thing that went wrong, kept here on purpose

Two gates were silently anti-conservative for about a week because the massing frame used a
bow-x/keel-z datum and the mesh used its own, differing by roughly 0.2 ft. Both gates passed
the whole time. A review caught it. Check your datums on every new gate, and treat a gate
that has never failed as unproven rather than safe.

## What is next

Phase 2.3b builds the flaperon geometry the current CLmax number assumes. Spar design is
gated on donor plans. Nothing structural is committed until then.

## License

Not yet chosen, so default copyright applies for the moment. Open an issue if you want to
use any of it and I will sort out a license.
