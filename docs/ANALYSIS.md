# VendorBridge: Plan Evaluation & Go/No-Go Analysis

Last updated: 2026-06-06
Author: review pass over `PLANNING.md` + `TASK.md` against all ground-truth sources.

---

## 0. TL;DR Verdict

**Proceed with `PLANNING.md` and `TASK.md`. They are correct, well-grounded, and aligned with what the judges actually reward. Do NOT spend more time on open-ended ideation or competitor research — you have hit diminishing returns there.**

But before you write the first line of application code, lock 4 decisions and apply ~6 targeted edits to the two files (listed in sections 5–7). The single biggest risk is **not** the idea — it is **scope vs. 8 hours**. The plan describes a product that is realistically a 2–3 day build; you must pre-commit to a "golden path" vertical slice so you always have a working demo.

Confidence: high. The plan covers 100% of the problem-statement requirements, captures the hidden Excalidraw differentiator (immutable audit log), and matches both the spoken video guidance and the **official** published Odoo hackathon criteria (verified online, see section 3).

---

## 1. What "ground truth" actually requires

Cross-checked the plan against four independent sources:

| Source | What it pins down |
|---|---|
| `Vendorbridge Hackathon Problem Statement.pdf` | 10 functional screens + 4 roles + the 8-step basic workflow |
| `VendorBridge - 8 hours.excalidraw` | 11 concrete screens with exact fields, INR/GST values, and the immutable-log instruction |
| `video-transcript.txt` | This event's reviewers' stated priorities ("most importantly, database design") |
| Official Odoo hackathon listing (verified online) | The actual scored "Must have" vs "Nice to have" criteria |

### Requirement coverage check (problem statement → plan)

Every required screen is present in the plan:

- Login/Signup + forgot password + session + validation + RBAC → covered (auth module, 4 roles).
- Dashboard (pending approvals, active RFQs, recent POs/invoices, analytics cards, quick actions) → covered.
- Vendor management (registration, status, categories, GST, contacts, search/filter) → covered.
- RFQ creation (title, items, qty, attachments, deadline, vendor assignment) → covered.
- Vendor quotation (pricing, delivery, notes, editable draft, submit) → covered.
- Quotation comparison (side-by-side, lowest-price highlight, delivery, rating, sort/filter) → covered.
- Approval workflow (approve/reject, remarks, timeline, state transitions) → covered.
- PO + invoice (auto PO number, tax/total calc, PDF download, print, email, status) → covered.
- Activity logs & notifications (RFQ/approval/invoice events, timeline, audit) → covered.
- Reports & analytics (vendor performance, stats, spend, monthly trends, export) → covered.

**Conclusion: no requirement is missing.** The plan is, if anything, a superset.

### Excalidraw fidelity check

Verified the Excalidraw text directly. The plan's seed data and screens match the mockup almost exactly: "Office Furniture procurement Q2", Ergonomic chair x25 / Standing desk x10, Infra Supplies / TechCore / OfficeNeed, grand total ₹2,00,010, CGST(9%)+SGST(9%), approval chain Submitted → L1 (Rahul Mehta) → L2 (Priya Shah) → Generate PO, and the audit screen note:

> "Audit logs must be immutable. These entries must be write-once, no edit or delete. Make sure your DB schema reflects this (no soft-delete on log records)."

This is verbatim in the file and the plan treats it as a first-class differentiator (hash-chained, append-only `activity_logs`, demo closer). **This is the highest-signal detail in the entire brief and the plan nails it.**

---

## 2. Strengths of the current plan (keep these)

1. **Database-first framing.** 18 normalized tables, FKs, indexes, state machines, and an append-only ledger. This is exactly the dimension the reviewers single out.
2. **Immutable audit ledger as the demo finale.** Directly answers the hidden instruction; cheap to build, high to score.
3. **Explainable Best Value Score** instead of fake "AI." Matches the criterion "use trendy tech only if it adds real value / understand it."
4. **India-native GST** (CGST/SGST vs IGST, GSTIN/PAN/HSN validation) — grounded in the Excalidraw, not invented.
5. **Honest scope tiers** (P0/P1/P2) and an explicit non-goals list.
6. **Local PostgreSQL, build-from-scratch, no BaaS** — matches the criteria precisely.
7. **Team Git workflow + per-member presentation ownership** — these are explicit scored items, and most teams forget them.

---

## 3. Important correction: what the judges actually score

I verified the official Odoo hackathon criteria online. They split into two buckets, and this changes emphasis slightly versus how the plan reads:

**MUST HAVE (hygiene — failing these loses points outright):**
- Real-time/**dynamic data**, not static JSON.
- **Responsive, clean UI** with consistent color scheme and layout.
- **Robust input validation.**
- **Intuitive navigation**, proper menu placement and spacing.
- **Proper team Git usage** (not one person owning the repo).

**NICE TO HAVE (differentiators — where you pull ahead):**
- **Backend API design, data modeling, local database.**
- Understanding AI/snippets (no blind copy-paste).
- Offline/local-first (don't depend on cloud).
- Trendy tech only if it adds real value.

### Why this matters for you

The video transcript (this event's reviewer) says "most importantly, database design," and your plan leaned hard into backend/DB. That instinct is right for *winning*. **But the published "must have" list is UI, validation, navigation, dynamic data, and Git** — i.e., the frontend/usability/process hygiene. A spectacular schema with a rushed, ugly, half-validated UI will still lose, because it fails the must-haves.

**Net:** Database design is your *differentiator*; clean responsive UI + validation + navigation + team Git are your *non-negotiables*. The current `TASK.md` says "build P0 backend endpoints before deep frontend polish" — that sequencing is dangerous if taken literally. Build in **vertical slices** (backend + a clean, validated UI for each feature together) so the must-haves are never left for the last hour.

### Two myths to drop from the proposals

- The arena proposal's "2022/2023 Odoo Experience hackathon winners did X" precedents are **not verifiable** (no public record of a procurement hackathon winner). Do **not** cite these in your pitch — judges may be Odoo engineers who will know.
- Real winners (e.g., the 2025 national runner-up) won on **architecture + resilience + presentation**, even with a live demo glitch — not on feature count. Reinforces: ship a tight, working, well-presented slice over a broad, fragile one.

---

## 4. The real risk: scope vs. 8 hours

This is the only place the plan is genuinely overcommitted.

- 18 tables, 12 backend modules, ~19 frontend routes, 5 state machines, plus Best Value Score, budget preview, 3-way match, hash chain, radar chart, reports, CSV export.
- Even a strong, well-coordinated team of 4 will struggle to finish **all of P0 + P1** in 8 hours, because P0 here is essentially the entire product.

The plan acknowledges this with tiers, but the tiers are still too generous. You need a smaller, explicit **golden path** that is the absolute must-finish — the spine of the demo — with everything else explicitly droppable.

### Recommended "Golden Path" (must work even if everything else is cut)

A single connected vertical slice:

1. Login as Procurement Officer, Vendor, Manager (auth + roles).
2. Officer creates the RFQ (2 line items) and assigns 3 vendors.
3. Vendor logs in, submits a quotation with GST.
4. Officer opens comparison → **lowest price highlighted** (the literal requirement) + Best Value Score.
5. Officer selects → approval initiated.
6. Manager approves with remarks.
7. PO generated → invoice generated with **CGST/SGST split**.
8. Invoice download/print + email-to-outbox, each action logged.
9. Activity page shows the **immutable, hash-linked** log with no edit/delete. (Demo closer.)

Everything not on this list — dashboard analytics depth, full reports/CSV, 3-way match, radar chart, budget preview, notifications bell, HSN edge cases — is **secondary** and should be time-boxed and dropped without hesitation if the golden path isn't solid.

### Suggested re-tiering for an 8-hour reality

- **Keep in must-ship:** the 9 golden-path steps above + clean responsive UI + validation + team Git.
- **High-value, cheap, keep early-P1:** immutable hash chain, Best Value Score, CGST/SGST split, lowest-price highlight, one dashboard with live counts, basic activity feed.
- **Demote to "only if ahead of schedule":** 3-way match lite, budget impact preview, radar chart, full reports + CSV export, notifications system, IGST path, HSN validation.
- **Stay in P2 (don't touch):** everything already in P2.

---

## 5. Decisions to lock BEFORE writing code

`PLANNING.md` section 15 and `TASK.md` section 2 still carry these as open questions. Carrying open questions into an 8-hour sprint is expensive. Resolve now:

1. **Custom app vs Odoo-native module → Custom app.** Justified: the criteria say "build from scratch," "design backend APIs / model data / local DB," and "plan for local solutions." Nothing requires an Odoo module, and learning Odoo's framework mid-sprint would burn hours. The clones are *reference only*. (If you can ask an organizer, confirm — but custom app is the correct default.)
2. **Stack → pick one and freeze it.** Default: FastAPI + SQLAlchemy + Alembic + PostgreSQL + React/Vite + TypeScript + Tailwind. Switch to Node/NestJS + Prisma **only** if the team is clearly faster in TypeScript end-to-end. Decide by team strength, not theory.
3. **Team size & ownership.** The 8-hour plan assumes ~4 people with clear lanes (DB/backend, frontend, integrator, QA/demo). Confirm headcount and assign lanes now.
4. **PDF/email scope → already decided correctly:** print-friendly HTML invoice first, real PDF only if time; email always to an `email_outbox` table. Keep. Deployment is **optional** (local is explicitly fine per criteria) — do not spend time deploying unless the golden path is done.

---

## 6. Specific edits to make to PLANNING.md / TASK.md

These are small, surgical, and worth doing before coding:

- **PLANNING.md §15 / TASK.md §2:** move "custom app" and "FastAPI+Postgres+React" from open questions to **Decided**, and add the team-size/lanes line.
- **PLANNING.md §3 / TASK.md §16:** insert the explicit **Golden Path** (section 4 above) as the top-priority must-ship, above P0, and mark 3-way match, budget preview, radar, full reports, notifications as "only if ahead."
- **TASK.md §4 (8-hour plan):** reword "build backend before frontend polish" → "build **vertical slices**: each feature ships with a clean, validated UI." Add a standing rule that the demo must be runnable end-to-end by the end of **every** hour from H4 onward.
- **PLANNING.md §10 / TASK.md:** add an explicit **responsive + navigation + validation** acceptance line per screen (these are official must-haves, currently under-emphasized).
- **PLANNING.md §14 (presentation):** add a note to **not** cite unverifiable "past hackathon winner" precedents; pitch on architecture, DB design, auditability, and the live working flow.
- **Both files:** standardize currency to ₹/INR everywhere (the mockup's dashboard "$ 2.3L" is an inconsistency in the source; use ₹).

Minor (optional): the Excalidraw RFQ status reads "published/sent" interchangeably — pick one term and use it consistently in code and UI.

---

## 7. Answer to "should I spend more time before coding?"

**No more research or ideation. Yes to a short, finite "execution-prep" step, then code.**

- Planning-first was the right call — it is literally what recent winners did (they wrote a strategy/project report before opening an editor). You have now reached the point of diminishing returns on *thinking*.
- The remaining valuable pre-code work is **converting the plan into execution assets**, not more analysis:
  1. Lock the 4 decisions in section 5.
  2. Apply the 6 edits in section 6.
  3. Write the actual **schema as migration files / Prisma schema** + a **seed script** (so Hour 1 is execution, not design).
  4. Scaffold the repo (backend + frontend + DB + README + `.env.example` + `.gitignore`) and set up the Git branch/lane convention.
  5. Pin the Golden Path demo script.
- Time-box this prep to ~30–45 minutes. Then start building, vertical slice by vertical slice, golden path first.

**Bottom line: the idea and plan are validated and winning-grade. Stop researching, lock the decisions, trim to the golden path, and start coding.**
