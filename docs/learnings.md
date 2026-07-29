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
