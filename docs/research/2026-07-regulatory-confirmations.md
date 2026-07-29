# Regulatory Confirmations Memo — Hull-as-Float Allowance & CA Bicycle Classification

**Date:** 2026-07-28
**Status:** Research Gate deliverable — informs but does not gate design (spec §2, §10, §11)
**Spec reference:** `docs/superpowers/specs/2026-07-28-sea-motorcycle-ultralight-design.md` §2 (regulatory
envelope), §5 (mass budget — float allowance held as unused reserve), §10 (risk register),
§11 (open questions)

> Every legal claim below carries a citation. Where a source is silent or the reading is
> contested, that is stated explicitly rather than resolved by inference.

---

## A. Hull-as-float weight allowance (14 CFR Part 103 / AC 103-7)

### Finding: NOT ambiguous on the core question — the provision was written for exactly this
### configuration. Residual ambiguity is narrower than the spec's risk register assumes.

**Primary source:** FAA Advisory Circular AC 103-7, "The Ultralight Vehicle" (1/30/1984),
fetched directly from `https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_103-7.pdf`
and OCR-extracted for verbatim text.

Paragraph **18.a** ("Items Excluded From the Computation of the Empty Weight of a Powered
Ultralight Vehicle") lists two categories of exclusion, each independently numbered:

- **18.a.(1) Safety Devices Which are Intended for Deployment in a Potentially Catastrophic
  Situation** — parachutes, up to 24 lb excluded without separate weighing (18.a.(1)(i)); no
  allowance if the parachute wasn't carried/attached at operation (18.a.(1)(ii)). This is the
  spec's +24 lb chute allowance (§2, §5) — squarely on point, no ambiguity.

- **18.a.(2) Floats Used For Landings On Water** — three sub-provisions:
  - **(i) Amphibious Floats** — up to 30 lb per detachable float excluded; attachment hardware
    to the airframe is *not* excluded and counts toward empty weight.
  - **(ii) Amphibious Fuselage** (verbatim): *"Where the fuselage is intended to function as a
    float during water landings, up to 30 pounds (the average weight of a single float) is
    allowed by the FAA to be excluded from the empty weight where the ultralight is capable of
    repeated water takeoffs and landings. (Operators may be required to demonstrate the water
    operational capability of their vehicle in order to receive an allowance for the added
    weight.) Up to 10 pounds per outrigger float and pylon is also allowed by the FAA."*
  - **(iii)** *"'Float' provisions not discussed here should be reviewed with FAA personnel at
    a Flight Standards field office."*

This is a direct, on-point match for sea-ez's configuration: a stepped planing hull that *is*
the float (spec §4, "Hull: single step, ~20° deadrise... Sealed foam-cored compartments;
positive flotation even holed"). AC 103-7 18.a.(2)(ii) exists specifically to cover flying-boat
hulls, not just detachable pontoons. Secondary confirmation: a Homebuilt Aircraft & Kit Plane
Forum thread paraphrases the same AC text independently ("designers may add 30 pounds... if the
ultralight uses a boat hull," plus "an additional 10 pounds... for each tip sponson") —
consistent wording, non-authoritative but corroborating.
(`https://www.homebuiltairplanes.com/forums/threads/part-103-and-floats.12531/`)

**What is NOT ambiguous:**
- The hull qualifies in principle. "Where the fuselage is intended to function as a float" is
  unambiguous plain-language coverage of a flying-boat hull.
- The allowance amount (30 lb) and the sponson add-on (10 lb per outrigger float and pylon) are
  stated in fixed dollar figures, not a percentage or formula requiring interpretation.

**What IS genuinely open (three narrower questions, not the headline one):**

1. **"Repeated water takeoffs and landings" — no defined test.** AC 103-7 doesn't specify how
   many landings, over what period, or what counts as documentation. Sub-clause (ii)
   parenthetical only says operators "may be required to demonstrate" capability — to whom,
   and by what standard, is undefined in the AC itself. Part 103 vehicles are not certificated
   or registered, so in practice there is no routine pre-flight FAA sign-off process to invoke
   this allowance against; it functions as an affirmative defense/rationale if weight is ever
   questioned (e.g., post-accident investigation), not a permit you apply for in advance. This
   is a real gap but doesn't threaten the underlying eligibility, only the paperwork trail.

2. **Do the spec's wing-mounted sponsons (§4: "Sponsons on outer wing panels... tucked in road
   mode, roll stability on water when spread. No separate hull sponsons") qualify as "outrigger
   float and pylon" under 18.a.(2)(ii)'s +10 lb/outrigger clause?** The AC's example language
   (and the forum's "tip sponson") suggests yes by analogy, but AC 103-7 doesn't define
   "outrigger float" precisely enough to confirm a wing-tip sponson (vs. a hull-mounted
   pontoon) counts. This matters only if the design ever needs that extra 10 lb reserve — per
   spec §5 the budget doesn't currently draw on any float allowance, so this is moot for the
   254 lb gate today.

3. **No FAA Office of Chief Counsel legal interpretation letter on this specific question was
   located.** I searched the FAA legal interpretations database index
   (`https://www.faa.gov/about/office_org/headquarters_offices/agc/practice_areas/regulations/interpretations`)
   and general web search; no interpretation letter addressing "amphibious fuselage" /
   flying-boat hull float allowance under Part 103 surfaced. Absence of an interpretation isn't
   evidence of a problem — the AC text is specific enough that a letter may never have been
   needed — but it means there's no case-specific precedent to point to if ever challenged.
   EAA's public Part 103 page (`https://www.eaa.org/eaa/aviation-interests/ultralights/getting-started-in-ultralight-flying/about-faa-part-103-for-ultralights`)
   restates the 254 lb rule but adds no interpretive detail beyond the regulation text itself —
   it is not a source of additional clarity here.

**Bottom line for the spec:** the risk register's framing ("Hull-as-float allowance
reinterpretation... Budget doesn't depend on it") is the right posture regardless of this
finding, but the finding itself is more favorable than "ambiguous" — the hull-as-float case is
the AC's named example, not an edge case being stretched to fit. The 17 lb margin held without
touching this allowance is a bonus safety factor, not a hedge against a shaky legal reading.

---

## B. California bicycle classification (California Vehicle Code)

### Finding: the pedal-only trike clears the bicycle definition on wheel count and the general
### vehicle-width statute does not appear to apply to bicycles by its own terms. No CVC section
### was found that caps a bicycle's width or length directly — that gap is flagged for
### confirmation, not resolved by silence.

**§231 — bicycle definition.** Verbatim, current text (confirmed via
`https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=VEH&sectionNum=231`,
amended by Stats. 2021, Ch. 311, effective 1/1/2022):

> "A bicycle is a device upon which a person may ride, propelled exclusively by human power,
> except as provided in Section 312.5, through a belt, chain, or gears, and having one or more
> wheels... An electric bicycle is a bicycle."

Two points relevant to sea-ez's road-mode trike:
- **Wheel count:** "having one or more wheels" — no upper bound, and specifically no wheel-count
  disqualifier. (An older wheel-diameter/frame-size formulation search-engine-summarized earlier
  in this research is **not** the current statute; the 2022 amendment simplified to the
  "one or more wheels" language quoted above. Cite the leginfo current text, not older
  paraphrases circulating online.) A three-wheeled, pedal-only trike is squarely covered.
- **Propulsion:** "propelled exclusively by human power" — the spec's design decision to drop
  e-hub motors for pedal drive (spec §5, "converts road classification from moped-question to
  bicycle-clean") is exactly the fact pattern this clause requires. §312.5 (motorized bicycle
  carve-out) doesn't apply since there's no motor in road mode.

**§670 — "vehicle" definition**, verbatim (confirmed via Justia/FindLaw cross-reference,
`https://law.justia.com/codes/california/code-veh/division-1/section-670/`):

> A "vehicle" is a device by which any person or property may be propelled, moved, or drawn upon
> a highway, excepting a device moved exclusively by human power or used exclusively upon
> stationary rails or tracks.

Because a human-power-only device is excluded from the CVC's definition of "vehicle," general
vehicle equipment/dimension statutes in CVC Division 15 (which regulate "vehicles") — including
**§35100** (total outside width of any vehicle or load shall not exceed 102 inches, with local
authority to restrict to 96 inches) — do not apply to bicycles **by the statute's own defined
terms**. Sea-ez's folded road-mode width (~5 ft / 60 in) is well under 102 in regardless, so this
is not a close call even if the exclusion argument is wrong. The width margin isn't the risk;
the *classification* is, and that turns on §670/§231, not on §35100's numeric limit.

**No CVC section was found that imposes a bicycle-specific width or length cap.** I searched
specifically for "bicycle width limit," "three-wheeled human-powered vehicle," and adjacent CVC
provisions and found none. This is stated as a negative finding, not a guarantee — CVC is large
and a narrower provision (e.g., in local municipal code, or a CVC section indexed differently)
could exist and wasn't surfaced by this search pass. The folded length (~18–19 ft) is unusual
enough for something self-identifying as a "bicycle" that it's worth a direct confirmation
rather than resting on the absence of a hit.

**§21202 — lane positioning**, verbatim summary of the substantive text (confirmed via
`https://codes.findlaw.com/ca/vehicle-code/veh-sect-21202/` and cross-checked against
`https://law.justia.com/codes/california/code-veh/division-11/chapter-1/article-4/section-21202/`):

> (a) Any person operating a bicycle upon a roadway at a speed less than the normal speed of
> traffic moving in the same direction... shall ride as close as practicable to the right-hand
> curb or edge of the roadway except [when passing, preparing for a left turn, avoiding unsafe
> conditions including a "substandard width lane," or approaching a right turn]. "Substandard
> width lane" is defined as "a lane that is too narrow for a bicycle and a vehicle to travel
> safely side by side within the lane."
> (b) On a one-way highway with two or more marked lanes, a bicyclist may ride as near the
> left-hand curb or edge as practicable.

This section governs *how* a bicycle is operated within a lane; it does not impose a dimensional
limit on the bicycle itself. The "substandard width lane" language is about the *roadway's*
width relative to car-plus-bike side-by-side travel, not a cap on the bike. Relevance to sea-ez:
a 5 ft-wide folded trike will functionally occupy most or all of a narrow neighborhood lane,
which is a *practical* operating consideration (ride assertively, expect to occasionally take
the full lane per the substandard-width-lane exception) rather than a legal violation risk. No
citation supports treating vehicle width itself as a §21202 violation.

**Net assessment:** the classification argument is stronger than "ambiguous" — §231 and §670
read together support bicycle status for a pedal-only, human-power-only trike regardless of its
unusual footprint. The open risk is not statutory text, it's **enforcement discretion**: a CHP
officer or local PD unfamiliar with an 18–19 ft, 5 ft-wide "bicycle" may stop and question it
regardless of what the code says, and that friction is worth pre-empting locally before the
1.5 mi road leg is ever ridden in public.

---

## Human-action checklist

The following require Ryan's direct outreach — they are not resolvable by further research and
are exactly the residual gaps identified above.

- [ ] **Ryan: email EAA government advocacy / EAA legal (via EAA membership channel) asking for
      their reading of AC 103-7 ¶18.a.(2)(ii) ("Amphibious Fuselage") as applied to a
      stepped-hull flying-boat design** — specifically (a) what "repeated water takeoffs and
      landings" demonstration would need to look like in practice, and (b) whether wing-mounted
      sponsons (not hull-mounted) plausibly qualify for the +10 lb/outrigger allowance. Frame
      as informational, not as seeking a ruling — Part 103 self-certifies.
- [ ] **Ryan: search or request access to the FAA Office of Chief Counsel legal interpretations
      database directly** (the index page returned a login/search wall to this session:
      `https://www.faa.gov/about/office_org/headquarters_offices/agc/practice_areas/regulations/interpretations`)
      for any interpretation letters referencing Part 103 float/fuselage weight allowances,
      since none were found via general web search.
- [ ] **Ryan: call the local CHP area office or city PD non-emergency line** (pick the
      jurisdiction covering the actual 1.5 mi road leg once the house-to-ramp route is fixed)
      and describe the folded machine's dimensions (~5 ft wide, ~18–19 ft long, pedal-only,
      3 wheels, no motor) — confirm they'd treat it as a bicycle under CVC §231/§670 before
      it's ridden on public roads. This is the one question statute text can't fully close:
      enforcement discretion in the field.
- [ ] **Ryan: confirm with CA DMV (phone or in-person) whether any registration/classification
      process exists for an unusual-footprint human-powered device** that might apply
      notwithstanding the §231/§670 bicycle reading above — DMV sometimes has informal
      practices not reflected in statute text alone.

---

## Sources

- FAA Advisory Circular AC 103-7, "The Ultralight Vehicle" (1/30/1984) — PDF fetched and
  OCR-extracted directly: `https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_103-7.pdf`
- FAA AC 103-7 index page: `https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentid/22640`
- EAA, "About FAA Part 103 for Ultralights": `https://www.eaa.org/eaa/aviation-interests/ultralights/getting-started-in-ultralight-flying/about-faa-part-103-for-ultralights`
- Homebuilt Aircraft & Kit Plane Forum, "Part 103 and floats" (corroborating, non-authoritative): `https://www.homebuiltairplanes.com/forums/threads/part-103-and-floats.12531/`
- FAA Office of Chief Counsel legal interpretations index (searched, no on-point letter found): `https://www.faa.gov/about/office_org/headquarters_offices/agc/practice_areas/regulations/interpretations`
- California Vehicle Code §231 (bicycle definition), current text: `https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=VEH&sectionNum=231`
- California Vehicle Code §670 (vehicle definition): `https://law.justia.com/codes/california/code-veh/division-1/section-670/`
- California Vehicle Code §35100 (vehicle width): `https://law.justia.com/codes/california/2005/veh/35100-35111.html`
- California Vehicle Code §21202 (bicycle lane positioning): `https://codes.findlaw.com/ca/vehicle-code/veh-sect-21202/` and `https://law.justia.com/codes/california/code-veh/division-11/chapter-1/article-4/section-21202/`

## What couldn't be verified

- No FAA Chief Counsel legal interpretation letter specific to Part 103 hull-as-float weight
  allowance was located (see human-action item above — the interpretations database itself
  needs direct/authenticated search, not general web search).
- No CVC section explicitly capping bicycle width or length was found; this is a negative
  result from a search pass, not a certified absence (see human-action CHP/DMV items).
- Did not independently verify USUA or USPPA guidance beyond what surfaced in general search —
  their primary sites did not return float-allowance-specific content in this pass.
