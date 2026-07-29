# Donor Selection — Research Gate Memo

**Date:** 2026-07-28
**Status:** Research Gate deliverable (spec §9, Track A milestone 1)
**Scope:** Selects the donor design(s) whose proven aero/structure numbers seed the
sea-motorcycle CadQuery baseline (spec §8, "Donor ingestion"). This memo does not
decide the fold-joint mechanical design itself — it identifies which donor's
published fold geometry and structural data to start from.

> Every number below carries a source URL or is tagged **"unverified — confirm
> from plans."** Spec numbers are cited by section, not restated as if independently
> derived.

## 1. Candidates researched

Per spec §9: **Kolb Firefly** (folding-wing donor), **Aerolite 103** (float
history), **Legal Eagle / Legal Eagle XL** and **Airbike** (structure philosophy).
No fifth candidate was added — none of the three researchers turned up a
better-documented Part 103 design with a folding wing *and* a float history than
these four; the closest alternates that surfaced during research (J&J Seawing,
Y2Fly Seahawk) are amphibious ultralights but returned no usable spec/structure
documentation, so they were not pursued further.

## 2. Comparison table

| | **Kolb Firefly** | **Aerolite 103** | **Legal Eagle / XL** | **Airbike (ISON/Jordan Lake Aero)** |
|---|---|---|---|---|
| Empty weight | 253–254 lb ([Wikipedia](https://en.wikipedia.org/wiki/Kolb_Firefly); [kolbaircraft.com](https://kolbaircraft.com/firefly.htm)) | 235 lb Part 103 config ([uflyit.com](https://www.uflyit.com/aerolite_103_specifications.htm)); Wikipedia gives a wider builder range 252–300 lb ([Wikipedia](https://en.wikipedia.org/wiki/Aero-Works_Aerolite_103)) | Legal Eagle 244 lb / XL 246 lb dry ([Wikipedia](https://en.wikipedia.org/wiki/Milholland_Legal_Eagle); [legaleagleairplane.com/legal-eagle-xl](https://legaleagleairplane.com/legal-eagle-xl/)) | 251–257 lb depending on engine ([Wikipedia](https://en.wikipedia.org/wiki/ISON_Airbike); [jordanlakeaero.com](https://www.jordanlakeaero.com/ultralight.html)) |
| Wingspan | 22 ft 0 in ([Wikipedia](https://en.wikipedia.org/wiki/Kolb_Firefly)) | 26 ft 10.25 in ([uflyit.com](https://www.uflyit.com/aerolite_103_specifications.htm)) | LE 23 ft 6 in / XL 26 ft 3 in ([Wikipedia](https://en.wikipedia.org/wiki/Milholland_Legal_Eagle)) | 26–26.75 ft ([Wikipedia](https://en.wikipedia.org/wiki/ISON_Airbike)) |
| Wing area | 117 sq ft ([Wikipedia](https://en.wikipedia.org/wiki/Kolb_Firefly); corroborated [Jane's/migavia](https://janes.migavia.com/usa/kolb/firefly.html)) | 121 sq ft manufacturer ([uflyit.com](https://www.uflyit.com/aerolite_103_specifications.htm)); Wikipedia gives 124 sq ft | LE 107 sq ft / XL 120.3 sq ft ([Wikipedia](https://en.wikipedia.org/wiki/Milholland_Legal_Eagle)) | 118–120 sq ft ([Wikipedia](https://en.wikipedia.org/wiki/ISON_Airbike)) |
| Airfoil | "Modified NACA 4412" — **single source only** ([Jane's/migavia](https://janes.migavia.com/usa/kolb/firefly.html)), not confirmed by manufacturer or a second source | Not published anywhere found — **unverified — confirm from plans** | Not published — **unverified — confirm from plans** | Not published — **unverified — confirm from plans** |
| Stall / cruise / max | 26 / 60 / 70 mph ([Wikipedia](https://en.wikipedia.org/wiki/Kolb_Firefly); [tailno.com](https://tailno.com/aircraft/kolb/models/firefly)) | 26–28 / 45–63 / 63 mph Part 103 config ([uflyit.com](https://www.uflyit.com/aerolite_103_specifications.htm)) | LE 25/50/60 mph, Vne 80; XL 27/~55–63/— ([Wikipedia](https://en.wikipedia.org/wiki/Milholland_Legal_Eagle)) | 28–30 / 55–63 / Vne 80 mph ([jordanlakeaero.com](https://www.jordanlakeaero.com/ultralight.html)) |
| Structure / spar material | "5-inch aluminum wing spar" (dimension only — no wall thickness, alloy, or load data published; [ultralightnews.com](http://www.ultralightnews.com/ultralight-aircraft-kolb-firefly/ultralight-aircraft-biggest-bang-2.htm)) | Aluminum tube frame + Dacron fabric, strut-braced, no dimensions published ([Wikipedia](https://en.wikipedia.org/wiki/Aero-Works_Aerolite_103); [EAA](https://www.eaa.org/eaa/aircraft-building/kits-and-plans/00---c/aero-lite-103)) | Wood I-beam spar: spruce cap strips + 1/8" ply web, spruce/ply ribs, 4130 steel-tube fuselage, aluminum struts/tail. XL wing derived from Mini-Max, **load-tested to +6G with no permanent deformation** ([Kitplanes](https://www.kitplanes.com/legal-eagle-xl/); [Wikipedia](https://en.wikipedia.org/wiki/Milholland_Legal_Eagle)) | Wood (spruce/plywood) parasol wing, fabric covered, 4130 steel-tube fuselage, sprung-tube gear. Spar schedule dimensions not published ([jordanlakeaero.com](https://www.jordanlakeaero.com/AirbikeLS.html)) |
| Part 103 compliance | Yes, at 253–254 lb standard build; BRS adds legal +24 lb per FAR 103.7 (cf. spec §5's own chute allowance) | Yes at 235 lb manufacturer config; Wikipedia's wider range suggests some builds exceed 254 lb | Yes, both variants under 254 lb dry | Yes, 251–257 lb depending on engine choice — narrowest margin of the four against the 254 lb ceiling |
| Folding wing | **Yes — standard.** Universal-joint pivot at wing root, wing stays attached through the fold, tail folds first, struts fold flat against wing underside, ~15 min by one person. No published fold-width/fold-length envelope. ([ultralightnews.com](http://www.ultralightnews.com/ultralight-aircraft-kolb-firefly/ultralight-aircraft-biggest-bang-2.htm); [kolbaircraft.com](https://www.kolbaircraft.com/)) | **No** — strut-braced, bolts apart for storage/transport but no in-field fold mechanism ([Wikipedia](https://en.wikipedia.org/wiki/Aero-Works_Aerolite_103)) | Not standard on either variant. An aftermarket fold mod is mentioned (~30 min fold) but is thinly sourced — **unverified** | **Yes — offered as a standard/optional feature** ("Folding wings, Brakes, wingtips, wheelpants optional" — [jordanlakeaero.com](https://www.jordanlakeaero.com/ultralight.html)). No mechanism description or fold-envelope numbers published. |
| Plans/kit/structural data availability | Kits/Plans listed by EAA ([eaa.org](https://www.eaa.org/eaa/aircraft-building/kits-and-plans/h---l/kolb-firefly)); factory sells "Factory Custom Air Quick-Build Kit," no published plans-only price found; forum thread on "plans/manuals" exists but returned HTTP 403, unread | Quick-build kit only (factory-assembled airframe kit), $19,450 ([uflyit.com](http://www.uflyit.com/aerolite_103_prices.htm)); no separate plans/structural-drawing product found | Plans-built. Legal Eagle plans package $190, XL package $215, from legaleagleairplane.com (price seen via search snippet, not a clean page render — confirm before treating as final) | Plans-built. Full plan set $150 (seen discounted to $95); Weld Package ~$2,850–2,950; Wood Wing Kit ~$2,675; Complete Airframe Kit ~$6,995–7,495, from [jordanlakeaero.com](https://www.jordanlakeaero.com/AirbikeLS.html) / [buildandfly.shop](https://buildandfly.shop/product/airbike-part103-ultralight/) |
| Float/seaplane fleet history | Confirmed on Puddle Jumper floats today, individual owner conversions (~$25–30k all-in, [Plane & Pilot](https://planeandpilotmag.com/kolb-firefly-ultralight-aircraft-on-puddle-jumper-floats-close-to-perfection/)). Predecessor Firestar has a documented amphibious mono-float ("Full Lotus") conversion ([ultralightnews.com](http://www.ultralightnews.com/sunfun2001/firestaramphib.htm)). No factory amphibious model, no fleet-scale count. | Float option confirmed to exist (U-Fly-It "used Puddle Jumper Floats for the past 20 years," [puddlejumper.com](https://www.puddlejumper.com/testimonials)) but **no Aerolite-specific float model, weight, or performance data published anywhere found** | **Not found** — no documented float/seaplane variant for either variant | **Not found** — no documented float/seaplane variant |
| Price (aircraft/kit) | No current factory list price published; historical 2003 figure $9,927 w/ engine (stale, [Jane's/migavia](https://janes.migavia.com/usa/kolb/firefly.html)); used partial kit sold for $6,000 ([Kitplanes](https://www.kitplanes.com/bilodeau-kolb-firefly/)); float-equipped all-in ~$25–30k | Complete Quick-Build Airframe Kit $19,450 + engine $7,404–$16,623 ([uflyit.com](http://www.uflyit.com/aerolite_103_prices.htm)) | Plans $190–215 (see above); full kit/build cost not itemized in sources checked | Plans $150; Complete Airframe Kit $6,995–7,495 (see above) |

### Gaps explicitly not found (do not treat as zero-data / do not guess)

- **No airfoil section is manufacturer-confirmed for any of the four candidates.** The Firefly's "Modified NACA 4412" is single-sourced (Jane's/migavia mirror) and unconfirmed by the manufacturer. All others: unpublished.
- **No candidate publishes a load-verified spar schedule** (tube wall thickness/alloy temper, or wood cap-strip/web dimensions with allowable loads) in any public source. The Legal Eagle XL is the sole exception with directional data: "+6G, no permanent deformation" is documented, but the underlying dimensions/load calc are not shown, only the summary claim.
- **No fold-width/fold-length envelope numbers exist publicly for either folding-wing candidate** (Firefly or Airbike) — both are described qualitatively only.
- Float-equipped empty weight is not published for the Firefly, and float model/weight/performance data is not published for the Aerolite despite the manufacturer confirming a float relationship exists.
- Two research threads returned inconclusive results and should not be treated as settled: the Kolb Firefly plans-manuals forum thread (HTTP 403, unread) and the Legal Eagle plans pricing page (search-snippet only, CSS-encoded on direct fetch).

## 3. Fold-mechanism transferability to an aft-fold on a hull

Spec §4 commits to a **"Kolb-style aft-fold wing: pivot at rear spar attach, wings
swing aft, leading edges outboard, resting in cradles alongside tail boom"**
(spec §4, "Key layout decisions"). The Firefly research above is broadly
consistent with that description but reveals one structural difference worth
flagging before CAD starts:

- The Firefly's pivot is a **universal joint at the wing root that stays attached
  through the fold** — the wing is never detached from the fuselage, only rotated.
  Struts disconnect at the fuselage end and fold flat against the wing underside.
  This is a **two-axis** pivot (the universal joint), not a simple single-hinge —
  worth reconciling against spec §4's "pivot at rear spar attach" language, which
  reads as a single hinge point. Confirm from Firefly plans whether the universal
  joint is doing double duty (fold + minor wing incidence adjustment) or is purely
  a fold pivot before committing the CAD parametrization.
- The Firefly's tail folds *first*, then the wings. On a hull-mounted
  configuration with a tail boom (spec §4) rather than a conventional aft
  fuselage, the fold sequencing and cradle geometry will need rework regardless —
  the Firefly stores wings "alongside the fuselage" on a taildragger airframe with
  ground clearance and geometry that doesn't exist on a planing hull. The
  **pivot principle transfers; the cradle/stowage geometry does not** and must be
  redesigned from the hull/tail-boom layout, not copied.
- The Airbike's folding-wing option is real but its mechanism is **completely
  undocumented publicly** (no description, no drawing, no video found). It cannot
  be evaluated as an alternative fold-mechanism donor without buying the plans —
  it is listed here for completeness, not recommended for structural adoption.
- No fold-width or fold-length numbers were found for the Firefly to validate
  against the spec's target folded envelope (spec §4: **"< 5 ft" folded width,
  ~18–19 ft folded length**). This must be confirmed from the purchased plans or
  measured from the demonstration video ([YouTube — Kolb Firefly wing and tail
  folding](https://www.youtube.com/watch?v=u5TKsH0EfFk)) before the CAD fold
  cradle geometry is finalized.

## 4. Recommendation

**Adopt a split-donor approach, consistent with spec §9's own framing ("Chosen
approach: A + B" / donor list already implies plans-built structure philosophy
matters separately from fold mechanism):**

- **Fold mechanism donor: Kolb Firefly.** It is the only candidate with a
  standard, well-marketed, single-person-operable fold mechanism with a
  documented pivot principle and a real float/fleet history to validate the
  concept on water. This matches spec §9's own rationale ("fleet-proven folding
  wing — the hardest part, already solved").
- **Structural/spar data donor: Legal Eagle XL, not the Firefly.** The Firefly's
  structural data is the thinnest of the four — a single unverified dimension
  ("5-inch aluminum spar") and no load data. The Legal Eagle XL is the only
  candidate with any independently documented load-test claim (+6G, no permanent
  deformation) and a legible built-up wood I-beam spar description (spruce cap
  strips + ply web) that is straightforward to reverse-engineer into a CadQuery
  parametric spar, consistent with spec §6's composite/foam-core philosophy
  (spar loads seed the laminate schedule, not the material itself — spec §6). The
  Legal Eagle XL's wing area (120.3 sq ft) also sits inside the spec's target
  135–150 sq ft range better than the Firefly's 117 sq ft once scaled, though
  scaling math is a CAD-phase task, not this memo's.
- **Aero/planform baseline: Kolb Firefly, with the caveat that its 117 sq ft wing
  area is below the spec's 135–150 sq ft target** (spec §3 already flags this:
  "donor planform expected to land in range — Kolb Firefly ≈ 130 sq ft" — note
  the spec's own estimate of ≈130 sq ft does not match this memo's sourced 117 sq
  ft; **reconcile this discrepancy before Track A milestone 2 CAD work begins**,
  since it affects whether the Firefly planform needs to be scaled up ~15–28%
  depending on which figure is right, or whether a different reference chord/span
  combination was intended).
- **Aerolite 103 and Airbike are not recommended as primary donors** but remain
  useful secondary references: Aerolite for float-option precedent (even though
  Aerolite-specific float data is unpublished, its manufacturer's 20-year Puddle
  Jumper relationship is a lead worth a direct phone call) and Airbike as a second
  data point that folding wings are achievable on a plans-built wood parasol wing,
  reinforcing (not replacing) the Firefly choice.

## 5. Concrete spar-data acquisition path

1. **Buy the Legal Eagle XL plans package from legaleagleairplane.com — $215**
   (price per search-snippet; **confirm on-site before purchase**, page did not
   render cleanly during this research — [legaleagleairplane.com](https://legaleagleairplane.com/legal-eagle-xl/)).
   This is the primary source for spar cap-strip/web dimensions, rib spacing, and
   the underlying data behind the published "+6G, no permanent deformation" claim.
2. **Contact New Kolb Aircraft Company directly** (Sales@kolbaircraft.com /
   customersupport@kolbaircraft.com, (606) 862-9692) to (a) obtain current
   plans/kit pricing (not published online), (b) request the fold-joint
   drawing/dimensions and the wing-root universal-joint detail, and (c) ask
   whether the "5-inch aluminum spar" claim found in secondary sources can be
   confirmed with wall thickness/alloy. This is the only path to real Firefly
   fold-geometry numbers — none exist publicly.
3. **Follow up on the unread Kolb Firefly "plans/manuals" forum thread**
   (homebuiltairplanes.com/threads/kolb-firefly-plans-manuals.52903/, HTTP 403
   during this research) via a logged-in account or direct browser visit — may
   contain community-sourced plans pricing or scans that shortcut step 2.
4. **Do not purchase Aerolite 103 or Airbike plans/kits** for spar data — the
   Aerolite is kit-only (no plans/structural drawings product found) and the
   Airbike's fold mechanism is undocumented and not the chosen donor for that
   subsystem; buying its $150 plan set is a possible fallback only if the Legal
   Eagle XL data proves insufficient for the wood-spar reverse-engineering task.

## 6. Open risks

- **Spec §3's ≈130 sq ft Firefly wing-area estimate vs. this memo's sourced
  117 sq ft is unreconciled.** If 117 sq ft is correct, the donor planform needs
  more scaling to reach the 135–150 sq ft target than the spec assumed. Resolve
  before CAD.
- **No candidate's spar data is verified without a plans purchase.** This memo's
  recommendation (Legal Eagle XL structure + Firefly fold) is a best-available
  call from public sources; it could change once the actual plans are in hand —
  e.g., if the Legal Eagle XL's wood spar load data doesn't scale cleanly to the
  higher gross weight and different load cases of a hull-mounted, sponson-equipped
  wing (spec §4: sponsons on outer wing panels add a load case the Legal Eagle
  never saw).
- **The Firefly's universal-joint pivot may not map cleanly to spec §4's "pivot
  at rear spar attach" single-hinge description** — needs reconciliation from
  purchased plans, not assumed compatible.
- **No fold-width/fold-length numbers exist to validate the Firefly against the
  spec's folded envelope target** (<5 ft width, 18–19 ft length, spec §4).
  Unverified until plans are purchased or the demo video is measured frame-by-frame.
- **Float weight/performance data is unpublished for every candidate.** The
  spec's "hull-as-float allowance" reasoning (spec §2) doesn't depend on any
  donor's float numbers, but the eventual sponson design (spec §4) would benefit
  from real float weight/drag data that this research could not source for any
  candidate.
- **Neither donor candidate has water/seaplane fleet history at the scale the
  Firefly does** — but even the Firefly's float history is individual owner
  conversions, not a factory-engineered amphibious variant. No candidate provides
  a validated water-handling baseline for the hull/step/spray-rail design (spec
  §4); that work remains fully original per spec §9 approach A ("design
  hull/chassis/fold-integration/systems clean").
- **Milholland Legal Eagle plans-source continuity is not fully verified** — the
  designer was confirmed alive and active as of July 2024 (Oshkosh, turning 100),
  contradicting an initial assumption that rights had changed hands; treat
  legaleagleairplane.com as the current authoritative source unless a direct
  purchase attempt proves otherwise.
