# Sea-Motorcycle Ultralight — Design Spec

**Date:** 2026-07-28
**Status:** Approved design, pre-implementation-plan
**Working name:** sea-ez (repo name TBD)

> **Safety notice:** This is a life-safety project. All aerodynamic and structural
> numbers herein are design targets, not validated engineering. Nothing flies until
> the proof-test gates in §10 pass. The builder is solely responsible for verifying
> every dimension, laminate schedule, and load path before flight.

## 1. Mission

A single-seat, straddle-ridden amphibious flying boat, legal under **FAR Part 103**,
that:

1. Self-propels ~1.5 mi of flat neighborhood road at bicycle speeds (pedal drive),
2. Enters the water at a public ramp, taxis out under engine power,
3. Takes off from protected water (Sacramento–San Joaquin Delta sloughs / inland
   lakes) and climbs to pattern altitude and above,
4. Completes the full cycle house → water → sky → water → house in one outing.

**Explicitly out of scope for v1:** SF Bay operations (Class B/C airspace under
FAR 103.17 + wind/chop unsuitable for a 254 lb seaplane), hydrofoils (parked for
v2), two-wheel self-balancing road mode, passenger capability (illegal under 103
anyway).

**Success criteria, in order:**
1. Rides the 1.5 mi road leg legally and un-terrifyingly.
2. Floats stably at rest with rider aboard.
3. Planes and lifts off in < 1,500 ft of water.
4. Climbs to pattern altitude with margin.
5. Full-cycle outing completed.

## 2. Regulatory envelope (design tyrant)

| Constraint | Value | Notes |
|---|---|---|
| Empty weight | 254 lb | Ballistic chute gets a separate +24 lb allowance (chute weight only). Hull-as-float allowance (~30 lb/float) treated as **reserve we do not plan to need** — legal interpretation is a Research Gate task. |
| Fuel | 5 US gal max | Fuel does not count toward empty weight; **batteries do**. |
| Max level speed | 55 kt | |
| Power-off stall | ≤ 24 kt | Sets wing area with gross weight. |
| Airspace | Class G/E only | Delta ops. No Class B/C/D or Class E surface areas without ATC authorization (functionally unavailable). |
| Road classification | CA **bicycle** (pedal-only, no motor) | No registration, no plate. Confirmation is a Research Gate task. |
| Pilot certificate | None required by 103 | Builder is a rated pilot; **seaplane instruction before first water flight is a hard project gate** (see Track B). |

## 3. Design point

- Design pilot + gear: **190 lb** → gross ≈ **470–500 lb**
- Wing area: **135–150 sq ft** (24 kt stall at ~490 lb with high-lift ultralight
  airfoil; note the Kolb Firefly is 117 sq ft per published specs — our wing
  scales UP from the donor planform; the 24 kt stall math governs, see
  docs/research/2026-07-donor-selection.md)
- Power: **28–35 hp gas pusher** (Vittorazi Moster 185 / Polini Thor class),
  premix 2-stroke, magneto ignition, pull start
- Cruise target: 45–55 kt (deliberately draggy is acceptable; 103 caps speed)
- Water takeoff: on the step and airborne inside 1,500 ft in calm conditions

## 4. Configuration

Stepped planing-hull fuselage, straddled semi-recumbent ("sport café lean" — rider
body is the CG trim mass in all modes, head always out of prop plane). High-mounted
aft-folding wing, pusher engine on pylon aft of wing root, tail boom with
conventional or inverted-V empennage clear of spray.

### Mode transformation matrix

| | Road | Water | Flight |
|---|---|---|---|
| Wings | Folded aft along hull, tips over tail boom | Folded (taxi) → spread + pinned before takeoff | Spread, pinned, verified |
| Wheels | Down; pedal drive | Retracted into hull sides above waterline | Retracted (water landing) |
| Prop | Stopped + brake, inside guard | Running (taxi/takeoff) | Running |
| Stability | Trike (2 mains + steerable nose) | Hull + wing-mounted sponsons | Wings |
| Pedals | Pedaling (bicycle mode) | Locked as pegs / rudder pedals | Rudder pedals |
| Handlebars | Steer nosewheel | Steer nosewheel + water rudder | Locked straight |

### Key layout decisions (settled)

- **Trike wheel layout**, not two-wheel balance. At bicycle speeds self-balancing
  gains nothing and adds drop risk. Still straddled/handlebar-steered — reads as
  a bike, won't fall over at the dock.
- **Kolb-style aft-fold wing:** pivot at rear spar attach, wings swing aft, leading
  edges outboard, resting in cradles alongside tail boom. Folded width **< 5 ft**;
  folded length ~18–19 ft.
- **Sponsons on outer wing panels** (Lake-amphib style): tucked in road mode,
  roll stability on water when spread. No separate hull sponsons.
- **Engine high on pylon, pusher:** prop out of spray, out of rider's world,
  behind fold envelope. Thrust-line pitch couple validated in OpenVSP.
- **Hull:** single step, ~20° deadrise forebody flattening aft, spray rails.
  Sealed foam-cored compartments; positive flotation even holed.

### Auxiliary foreplane ("sport canard") — removable module

A **true lifting-canard configuration is rejected**: the canard-stalls-first
requirement caps main-wing CL and fights the 24 kt stall rule, and a bow-mounted
lifting surface takes spray/wave strikes (rain/contamination lift-loss is the
known canard failure mode).

Instead: a **small fixed foreplane, ~4–6 sq ft, mounted high on the bow**, well
clear of the static waterline. Functions:
1. **Rotation authority** — counters the high-pylon pusher's nose-down thrust
   couple exactly where the configuration is weakest (rotating off the step at
   low airspeed).
2. Trim + aesthetics.

Constraints: sized in OpenVSP so it can never stall the aircraft or mask the main
wing; **bolt-on, removable (four bolts)**; v1 first flights occur WITHOUT it;
added only after baseline envelope is known; removed if it misbehaves.

## 5. Mass budget (contract — enforced by CI)

Target: airframe-without-chute ≤ **254 lb**; chute ≤ 24 lb under its own allowance.
Float allowance untouched (deep reserve).

| Group | Budget (lb) |
|---|---|
| Wing (spar, ribs, skin, fold fittings, sponsons) | 62 |
| Hull/chassis (step, keel, seat, bulkheads) | 55 |
| Tail boom + empennage | 16 |
| Foreplane module (removable) | 4 |
| Engine (Moster 185 class) + mount + exhaust | 34 |
| Prop + full-perimeter guard ring | 8 + 4 |
| Fuel system (5 gal tank, lines, dry) | 4 |
| Landing gear: 3 wheels, retract links, brakes | 22 |
| Pedal drivetrain (crank, chain, freewheel, granny gearing) | 9 |
| Controls (stick, cables, pedal/rudder mechanism) | 8 |
| Instruments (mechanical ASI, RAM mount, BLE sensors, sensor battery) | 1.5 |
| Accessory 12V ~50 Wh pack (strobe, BLE, phone charge — removable) | 1.5 |
| Hardware, paint, misc | 8 |
| **Airframe subtotal (counts against 254)** | **≈ 237** |
| Ballistic parachute (own +24 allowance) | 22 |
| **Margin against 254** | **≈ 17 lb** |

Budget rules:
- Every CadQuery part carries material + computed mass.
- **CI fails the build if the rollup exceeds 254 (chute excluded).**
- First composite builds run 5–10 % heavy vs CAD; the margin exists to absorb
  that, not to fund features.

### Decisions that bought the margin
- **Pedal drive replaces e-hub motors + battery** (−19 lb hardware, +9 lb
  drivetrain, net −10): 1.5 mi flat road leg at 5–8 mph is cargo-trike effort;
  accepted as "stately." Also converts road classification from moped-question
  to bicycle-clean.
- **OpenEFB replaces the panel** (see §7): −3.5 lb vs gauge panel.

## 6. Structures, materials, fabrication

- **Philosophy:** Rutan-lineage moldless composite — foam-core sandwich with
  carbon skins (hull, wing skins); carbon cap strips over foam shear web (spars).
  Wet layup + vacuum bag, garage-temp cure with elevated post-cure. No autoclave,
  no prepreg. Donor spar loads seed the laminate schedule.
- **CNC:** 4-axis hot-wire foam cores (wing, bulkheads, foreplane) from
  toolchain-generated G-code. Flight-critical metal (fold fittings, root pins,
  engine mount, chute hardpoints) machined by a local CNC shop from a drawing
  package with specified alloy and dye-penetrant inspection — not garage tolerance.
- **3D printing:** jigs, small-part molds, fairings, prop-guard segments,
  instrument pods only. **Printed polymer is forbidden in primary structure**
  (creep + UV + water). Toolchain enforces via part classification flag.
- **Fold joint = most safety-critical assembly:** donor-derived geometry, machined
  fittings, positive-lock pins with visual + tactile verification windows,
  "cannot look assembled unless it is" design feature. Dedicated static proof rig
  before it ever carries the wing in flight.
- **Flotation:** ≥ 4 sealed foam-filled bays; total foam buoyancy > 1.5× gross.

## 7. Systems

- **Flight controls:** conventional 3-axis. Center stick between knees (no
  handlebar flight controls — negative-transfer trap across modes). Handlebars
  steer nosewheel + water rudder only; lock straight in flight. Rudder via the
  pedal shaft: pedals lock into pegs detent for water/flight and pivot as rudder
  pedals.
- **Fuel:** single 5-gal rotomolded tank behind seatback at CG, gravity feed,
  squeeze-bulb prime, sight tube. Premix (no oil injection).
- **Ballistic chute:** softpack BRS-class canister on engine pylon, rocket vector
  clear of prop and folded wings, bridle to hull hardpoints. Repack schedule in
  maintenance log from day one.
- **Prop guard:** full-perimeter ring with mesh aft of rider zone.
  Non-negotiable (dock, road, swimmers).
- **Electrical:** none required for flight. Removable 12V ~50 Wh accessory pack.
- **Water systems:** kick-down water rudder (bar-linked), bilge sponge + hand
  pump, molded bow cleat + 20 ft line.

### Avionics: OpenEFB as the panel

- **First flight:** mechanical ASI (~0.3 lb, works wet/hot/sun/battery-dead) is
  the one steam gauge. Airspeed is life-critical at 24 kt stall; GPS groundspeed
  is not airspeed.
- **Primary display:** phone/iPad running **OpenEFB "panel mode"** (new feature):
  full-screen IAS/ALT/EGT tapes + moving map, sunlight-legible, glove-tappable.
  Replaces altimeter, moving map/airspace (Delta G/E boundaries), GPS, logging.
- **Committed upgrade path:** ESP32 **BLE pitot-static module** feeding IAS to
  OpenEFB, and **BLE EGT/CHT sensor** on the 2-stroke (seizure precursors show in
  EGT first — single engine over water).
- **Part 103 note:** mounted portable devices are removable equipment — reasonable
  reading is they don't count toward empty weight (as with handheld radios).
- **Zero build dependency:** the aircraft never waits on software; the mechanical
  ASI guarantees that.
- Companion workstream in separate repos (OpenEFB + sensor firmware), separate
  timeline.

## 8. Toolchain (plans-as-code from day one)

Fork **open-ez** → new repo (this one):

- **CadQuery SSOT:** every part parametric with material + computed mass.
- **CI gates:** empty-weight rollup ≤ 254 (test, not a spreadsheet); OpenVSP
  static margin (with/without foreplane), stall behavior, thrust-line pitch
  couple; folded-CG road-mode tipover check; hull hydrostatics (waterline,
  righting moment with rider).
- **Manufacturing outputs:** hot-wire G-code (cores), DXF packages (CNC-shop
  metal), STL (jigs/fairings). `primary_structure / secondary / non_structural`
  classification flag enforces the no-printed-primary rule at generation time.
- **Donor ingestion:** donor geometry + published specs encoded as the baseline
  parameter set — v2/v3 clean-sheet becomes parameter evolution, not a restart.

## 9. Approach & phase plan

**Chosen approach: A + B.**
- **A — "Donor aero, custom body":** adopt proven aero/structure numbers
  (airfoil, planform, spar schedule, tail volumes, CG envelope) from a documented
  Part 103 design; design hull/chassis/fold-integration/systems clean. Donor
  candidates for the Research Gate: **Kolb Firefly** (fleet-proven folding wing —
  the hardest part, already solved), **Aerolite 103** (legal 103 w/ float option),
  Legal Eagle / Airbike families for structure philosophy.
- **B — Buy & fly (parallel track, starts now):** seaplane/ultralight-float
  instruction, then a used Firefly-class ultralight (~$8–15k) flown in the Delta —
  trainer, reference article, and envelope-truth for every Track A number.

### Track A milestones

1. **Research Gate** (~1–2 mo): donor selection + spar data; hull-as-float
   allowance interpretation (EAA/USUA); CA bicycle classification confirmation;
   Delta launch-site survey.
2. **Design in code** (~4–6 mo): full CadQuery model passing all CI gates;
   foreplane sized in OpenVSP.
3. **Component proof** (~3–4 mo): fold-joint rig (500 load cycles under load),
   wing static test to **+4 g / −2 g**, hull section water-soak + impact coupons.
4. **Build** (~8–14 mo): hull → wing → integration.
5. **Test campaign** — one variable at a time: road mode → flotation/static
   stability → displacement taxi → step taxi (flying speed, never leaving water)
   → crow hops in ground effect → first circuit → **then** foreplane module →
   **then** envelope expansion to pattern altitude.

## 10. Risk register

| Risk | Mitigation |
|---|---|
| Weight creep | CI mass gate + ~17 lb margin + float-allowance deep reserve |
| Fold-joint failure | Proof rig, 500 cycles, inspection windows, positive-lock pins |
| Glassy-water landing misjudgment (classic seaplane killer) | Track B training before any Track A water ops |
| 2-stroke seizure over water | EGT/CHT monitoring; always-within-glide-of-landable-water rule |
| Hull-as-float allowance reinterpretation | Budget doesn't depend on it (margin held without) |
| Printed-part misuse in structure | Toolchain classification flag, generation-time enforcement |
| Wind/sail-area on folded-wing road leg | Accepted (1.5 mi); no-go call on high-wind days |

## 11. Open questions (Research Gate inputs, not blockers to planning)

- Final donor selection and spar-data acquisition path.
- FAA/EAA interpretation of hull-as-float weight allowance for a flying-boat hull.
- CA DMV confirmation that a pedal-only three-wheeler of this footprint is a
  bicycle (footprint/width limits on bike classification).
- Delta launch-site shortlist (ramp grade, slough width, prevailing wind).
- Repo name.
