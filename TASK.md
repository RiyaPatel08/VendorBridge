# VendorBridge TASK.md

Last updated: 2026-06-06

This file tracks current work, milestones, backlog, implementation tasks, discoveries, risks, and demo preparation for Team BuzzBeatStrong's VendorBridge hackathon build.

## 1. Current Status

- [x] Problem statement reviewed.
- [x] Excalidraw screens reviewed.
- [x] Instructional video transcript incorporated into technical priorities.
- [x] Sonnet, Arena, Codex, and mentor proposals compared.
- [x] Final hybrid direction selected.
- [x] Relevant cloned repositories inspected.
- [x] High-level architecture chosen.
- [x] P0/P1/P2 scope defined.
- [x] Final team stack confirmed (FastAPI + SQLAlchemy + Alembic + PostgreSQL + React + TS + Vite + Tailwind + Redis).
- [x] Database choice decided (PostgreSQL; SpacetimeDB/DuckDB/Convex rejected).
- [x] Redis caching and blockchain-style ledger decided.
- [x] VendorBridge IQ Overview folded into scope.
- [x] Team size confirmed (4) and ownership assigned (see section 1.5).
- [x] Repository scaffold created.
- [x] PostgreSQL + Redis (Docker Compose) initialized.
- [x] First migration created.
- [ ] End-to-end RFQ-to-invoice golden-path demo implemented.

## 1.5 Team Roster and Ownership

Four members. Each owns a vertical (backend + frontend for their area) so everyone can demo and present their part (team collaboration is a scored criterion). Foundation work (M1) lands first to unblock the others. Owners are responsible, but pairing is encouraged.

### M1 - Platform and Ledger Lead

- Repo scaffold, Docker Compose (PostgreSQL + Redis), lint/format, README, `.env.example`, `.gitignore`.
- Database schema, Alembic migrations, seed script (depended on by everyone).
- Auth + RBAC + sessions/JWT + password hashing.
- Blockchain-style immutable ledger: hash chain, Merkle block sealing, DB triggers (no update/delete), integrity-verification endpoint, and the shared activity-logging service all modules call.
- Redis cache helpers + login rate limiting.
- Frontend: login/register, app shell + sidebar navigation + theme, Activity & Logs page (with live integrity verify).

### M2 - Vendor Domain and Marketplace Lead

- Vendors CRUD, GSTIN/PAN validation, categories, status.
- Vendor lifecycle (5 stages) + reputation scores + multi-criteria ratings (post-delivery).
- Vendor discovery engine (fair RFQ distribution).
- Vendor portal actions: PO acceptance (accept/reject/request modification) and delivery tracking updates.
- Frontend: Vendors list/detail, vendor lifecycle/compliance badges, vendor portal screens.

### M3 - Sourcing and Intelligence Lead

- RFQ creation, line items, vendor assignment, invites.
- Quotation submission incl. partial-fulfillment fields.
- Comparison + Best Value Score + radar chart + coverage display.
- Procurement risk engine (Low/Medium/High, 5 dimensions).
- Split procurement engine (P1-stretch).
- Frontend: RFQ create, quotation form, comparison screen, split-recommendation UI.

### M4 - Approvals, Documents and Insights Lead

- Approval workflow (tiers, remarks, budget impact, risk display).
- PO generation (incl. split POs) + buyer delivery view + receipt confirmation.
- Invoice generation + GST split + PDF/print/email outbox + 3-way match lite.
- Dashboard + Reports/analytics (incl. vendor growth) + CSV export + charts.
- Frontend: approval screens, PO/invoice documents, dashboard, reports.
- Owns the demo script and end-to-end integration QA.

### Shared rules

- Every state transition calls M1's activity-logging service.
- Build vertical slices: backend + clean validated UI together; never leave UI to the last hour.
- The golden path (section 16) must run end to end by the end of every hour from Hour 4.

## 2. Immediate Next Steps

Do these first, in order.

- [x] Build type decided: custom app (not an Odoo module).
- [x] Stack confirmed: FastAPI + SQLAlchemy + Alembic + PostgreSQL + React + TS + Vite + Tailwind + Redis.
- [x] Create the actual project repository/folder outside `clones-odoo`.
- [x] Add README with setup commands and demo credentials.
- [x] Add `.env.example`.
- [x] Add Git branch naming convention and assign ownership.
- [x] Set up PostgreSQL + Redis locally via Docker Compose.
- [x] Create initial database migration for core tables (incl. lifecycle, ratings, risk, split/delivery fields, ledger + ledger blocks).
- [x] Seed demo users, vendors (across all lifecycle stages), RFQ, quotations, approval, PO, invoice, and activity logs.
- [ ] Build vertical slices (backend + clean validated UI together), golden path first.

## 3. Milestones

### Milestone 0: Project Setup

Goal: Clean repo, local DB, migrations, seed script, and team workflow.

- [x] Create project structure.
- [x] Initialize Git.
- [x] Add `.gitignore`.
- [x] Add backend framework.
- [x] Add frontend framework.
- [x] Add PostgreSQL connection.
- [x] Add migration tool.
- [x] Add seed command.
- [x] Add lint/format commands.
- [x] Add basic health check endpoint.
- [x] Add README setup instructions.

Acceptance:

- A teammate can clone, run setup, migrate DB, seed data, and open the app locally.

### Milestone 1: Database Foundation

Goal: Show strong relational data design.

- [x] Create `users`.
- [x] Create `vendors` (incl. lifecycle stage, reputation scores, verification flags).
- [x] Create `vendor_ratings`.
- [x] Create `vendor_categories`.
- [x] Create `rfqs`.
- [x] Create `rfq_items`.
- [x] Create `rfq_vendor_invites`.
- [x] Create `quotations`.
- [x] Create `quotation_items`.
- [x] Create `approval_requests`.
- [x] Create `approval_steps`.
- [x] Create `budgets`.
- [x] Create `purchase_orders`.
- [x] Create `purchase_order_items`.
- [x] Create `invoices`.
- [x] Create `invoice_items`.
- [x] Create `activity_logs`.
- [x] Create `activity_log_blocks`.
- [x] Create `notifications`.
- [x] Create `email_outbox`.
- [x] Add indexes.
- [x] Add foreign key constraints.
- [x] Add enum/status constraints.
- [x] Add no-update/no-delete trigger for `activity_logs` and `activity_log_blocks` (committed).

Acceptance:

- Schema can model the full RFQ -> Quote -> Approval -> PO -> Invoice -> Audit flow without static JSON.

### Milestone 2: Auth and Roles

Goal: Secure login and role-based access.

- [x] Registration endpoint.
- [x] Login endpoint.
- [x] Password hashing.
- [x] Session/JWT generation.
- [x] Current user endpoint.
- [x] Role guard middleware.
- [x] Frontend login screen.
- [x] Frontend registration screen.
- [x] Role-based redirects.
- [x] Forgot password placeholder with validation.

Acceptance:

- Admin, procurement officer, vendor, and manager users can log in and see only the correct routes/actions.

### Milestone 3: Vendor Management

Goal: Vendor records, GST/PAN validation, filters, and statuses.

- [x] Vendor list API with pagination/filter/search.
- [x] Create vendor API.
- [x] Update vendor API.
- [x] Vendor detail API.
- [x] Block/unblock vendor action.
- [x] GSTIN validator.
- [x] PAN validator.
- [x] Category management or seeded categories.
- [x] Vendor list UI.
- [x] Add/edit vendor form.
- [x] Vendor status badges.
- [x] Compliance badge.

Acceptance:

- Procurement Officer/Admin can create and manage vendors with valid India procurement fields.

### Milestone 4: RFQ Creation

Goal: RFQ creation with line items and vendor assignment.

- [ ] RFQ create API.
- [ ] RFQ update draft API.
- [ ] RFQ send API.
- [ ] RFQ list/detail API.
- [ ] RFQ line item validation.
- [ ] Vendor assignment table.
- [ ] Invite token generation.
- [ ] Activity log on create/send/vendor invite.
- [ ] RFQ list UI.
- [ ] RFQ create form UI.
- [ ] Line item editor.
- [ ] Vendor multi-select.
- [ ] Save draft.
- [ ] Save and send.

Acceptance:

- Officer can create "Office Furniture Procurement Q2", add two items, assign three vendors, and send the RFQ.

### Milestone 5: Vendor Quotation Submission

Goal: Vendors can submit quotes against assigned RFQs.

- [ ] Vendor RFQ list API.
- [ ] Vendor RFQ detail API.
- [ ] Quotation draft create/update API.
- [ ] Quotation submit API.
- [ ] Quotation line item totals.
- [ ] GST calculation.
- [ ] Deadline guard.
- [ ] Activity log on draft save and submit.
- [ ] Vendor portal RFQ list UI.
- [ ] Vendor quotation form UI.
- [ ] Live subtotal/GST/grand total.
- [ ] Save draft button.
- [ ] Submit quotation button.

Acceptance:

- Vendor can log in, view assigned RFQ, save a draft, and submit a quotation before the deadline.

### Milestone 6: Quotation Comparison

Goal: Procurement can compare quotes and select a vendor.

- [ ] Comparison API for RFQ.
- [ ] Lowest price calculation.
- [ ] Fastest delivery calculation.
- [ ] Best Value Score calculation.
- [ ] Score breakdown.
- [ ] Sort and filter.
- [ ] Select quotation API.
- [ ] Activity log on selection.
- [ ] Comparison table UI.
- [ ] Lowest price highlight.
- [ ] Score bars or radar chart.
- [ ] Select and approve action.

Acceptance:

- Officer can compare three quotations and select a quote based on both price and Best Value Score.

### Milestone 7: Approval Workflow

Goal: Manager can approve/reject with policy context and budget impact.

- [ ] Approval request creation after quote selection.
- [ ] Threshold-based approval route.
- [ ] Policy reason generation.
- [ ] Budget impact calculation.
- [ ] Approval detail API.
- [ ] Approve endpoint.
- [ ] Reject endpoint.
- [ ] Remarks validation.
- [ ] Approval timeline.
- [ ] Activity log on approval request/approval/rejection.
- [ ] Approval list UI.
- [ ] Approval detail UI.
- [ ] Budget Impact Preview component.
- [ ] Policy reason badges.
- [ ] Approval stepper.

Acceptance:

- Manager sees quote summary, budget impact, policy reasons, approval chain, and can approve or reject with remarks.

### Milestone 8: Purchase Order and Invoice

Goal: Approved quotation generates official PO and invoice.

- [ ] Generate PO endpoint.
- [ ] PO number generation.
- [ ] PO line copy from quotation.
- [ ] PO list/detail API.
- [ ] Generate invoice endpoint.
- [ ] Invoice number generation.
- [ ] Invoice tax totals.
- [ ] Invoice list/detail API.
- [ ] Invoice status update.
- [ ] Download/print action logging.
- [ ] Email invoice action writes to `email_outbox`.
- [ ] PO detail UI.
- [ ] Invoice detail UI.
- [ ] Print-friendly invoice layout.
- [ ] Download PDF or printable HTML.
- [ ] Email invoice button.

Acceptance:

- After approval, the app generates a PO and invoice with GST totals and logs download/print/email actions.

### Milestone 9: 3-way Match Lite

Goal: Show ERP maturity before invoice is payable.

- [ ] Add received quantity to PO item.
- [ ] Add accepted quantity to PO item.
- [ ] Match check service.
- [ ] Block payable status if mismatch.
- [ ] Override or warning if time permits.
- [ ] 3-way match UI card.
- [ ] Activity log on match/pass/fail.

Acceptance:

- Invoice can be marked payable only when PO quantity, accepted quantity, and invoice quantity/amount match.

### Milestone 10: Blockchain-style Immutable Ledger and Notifications (Owner: M1)

Goal: Make the audit trail a visible, verifiable differentiator.

- [ ] Activity ledger service (shared, called by all modules).
- [ ] Canonical payload builder.
- [ ] Hash generation (`entry_hash` from canonical fields + `previous_hash`).
- [ ] Previous hash lookup + append-only create method.
- [ ] Merkle block sealing into `activity_log_blocks` (every N entries + on demand).
- [ ] Optional server-signature over entry/block hashes.
- [ ] No update/delete routes.
- [ ] DB trigger rejecting UPDATE and DELETE on ledger tables (committed, not optional).
- [ ] Integrity-verification endpoint (recompute chain + Merkle roots, return PASS/FAIL).
- [ ] Notification creation for user-facing alerts.
- [ ] Activity page API + notification list API.
- [ ] Activity page UI + timeline UI.
- [ ] Hash chain + block fields visible in detail drawer.
- [ ] "Verify integrity" button in UI.
- [ ] No edit/delete controls on logs.

Acceptance:

- Activity page proves logs are write-once and hash-linked, and the verify button confirms chain integrity live.

### Milestone 11: Dashboard and Reports

Goal: Show live procurement metrics from database.

- [ ] Dashboard stats API.
- [ ] Pending approvals widget.
- [ ] Active RFQs widget.
- [ ] Recent POs widget.
- [ ] Recent invoices widget.
- [ ] Spending trend query.
- [ ] Reports API.
- [ ] Vendor performance query.
- [ ] Spend by category query.
- [ ] Monthly trend query.
- [ ] CSV export endpoint.
- [ ] Dashboard UI.
- [ ] Reports UI.
- [ ] Charts.
- [ ] Export button.

Acceptance:

- Dashboard and Reports display dynamic DB-backed data, not hardcoded JSON.

### Milestone 13: Vendor Lifecycle, Reputation and Discovery (Owner: M2)

Goal: Turn vendors into a growth marketplace (core IQ identity).

- [ ] `lifecycle_stage` derivation from `completed_orders_count`.
- [ ] `vendor_ratings` table + post-delivery rating API (4 criteria).
- [ ] Reputation score computation (reliability, delivery, completion, satisfaction, composite).
- [ ] Lifecycle progression + ledger event on stage change.
- [ ] Vendor discovery engine API (fair mix of established + new vendors).
- [ ] `discovery_source` + stage snapshot recorded on invites.
- [ ] Lifecycle badges + reputation display in vendor UI.
- [ ] Discovery suggestions surfaced in RFQ vendor assignment.

Acceptance:

- Seeded vendors show different lifecycle stages; creating an RFQ suggests a fair mix; a completed+rated order moves a vendor up a stage.

### Milestone 14: Procurement Risk Engine (Owner: M3)

Goal: Replace bare policy badges with a named risk tier for managers.

- [ ] Risk computation across 5 dimensions (verification, delivery reliability, inventory availability, vendor history, price abnormality).
- [ ] Map to Low/Medium/High + store `risk_breakdown`.
- [ ] Risk tier + breakdown on approval/risk screen.
- [ ] Ledger event for risk assessment.

Acceptance:

- Manager sees a Low/Medium/High risk tier with a per-dimension breakdown before approving.

### Milestone 15: PO Acceptance and Delivery Tracking (Owner: M2 + M4)

Goal: Add vendor collaboration and order visibility.

- [ ] Vendor PO acceptance API (accept / reject / request modification).
- [ ] Delivery status updates (packed -> shipped -> in transit -> delivered).
- [ ] Buyer receipt confirmation sets PO `received`.
- [ ] Vendor portal acceptance + delivery UI.
- [ ] Buyer delivery tracking view.
- [ ] Ledger events for acceptance and each delivery step.

Acceptance:

- Vendor accepts a PO and walks it through delivery; buyer sees real-time status.

### Milestone 16: Partial Fulfillment and Split Procurement (Owner: M3) - P1-stretch

Goal: The flashiest IQ feature. Build only after the golden path and Milestones 13-15 are stable.

- [ ] Partial-fulfillment fields on quotation items (available now / additional / lead time).
- [ ] Coverage display in comparison.
- [ ] Split allocation engine (greedy fill across vendors).
- [ ] Split PO generation with `split_group_id` + `split_label` + suffixed PO numbers.
- [ ] Split invoices + independent delivery per split PO.
- [ ] Split-recommendation UI.

Acceptance:

- An RFQ that no single vendor can fully cover produces a recommended split across vendors with PO-...A / PO-...B.

### Milestone 17: Redis Caching and Rate Limiting (Owner: M1)

Goal: Defensible performance/scalability layer.

- [ ] Redis connection + cache-aside helpers.
- [ ] Cache dashboard/report aggregates with invalidation on relevant writes.
- [ ] Login rate limiting.
- [ ] Optional session/reputation caching.

Acceptance:

- Repeated dashboard/report loads hit cache; cache invalidates correctly on writes; login is rate-limited.

### Milestone 12: Polish, Testing, Demo

Goal: Stable presentation.

- [ ] Seed realistic demo dataset.
- [ ] Add demo credentials to README.
- [ ] Run end-to-end demo flow at least twice.
- [ ] Fix broken navigation.
- [ ] Fix validation messages.
- [ ] Fix responsive layout issues.
- [ ] Add loading and empty states.
- [ ] Add toast notifications.
- [ ] Run lint/format.
- [ ] Run backend tests.
- [ ] Prepare 5-minute demo script.
- [ ] Prepare backup screenshots/video if possible.
- [ ] Assign presentation sections to every teammate.

Acceptance:

- Demo can run smoothly without manual database edits.

## 4. 8-hour Build Plan (4 parallel lanes)

Each hour lists work per member (M1-M4). The golden path is the priority; IQ/stretch items only proceed when the golden path for that hour is green. Merge to main frequently.

### Hour 1: Foundation

- M1: Repo scaffold, Docker Compose (Postgres + Redis), full schema + first migration, seed skeleton, health check, ledger service stub + DB triggers.
- M2: Vendor model/fields finalized with M1; GSTIN/PAN validators.
- M3: RFQ/quotation/comparison API contracts drafted against the schema.
- M4: Frontend app shell, sidebar nav, theme, routing, auth screen scaffolds, API client + demo-story draft.

### Hour 2: Auth + Vendors

- M1: Auth + RBAC + sessions + password hashing; wire ledger service.
- M2: Vendor CRUD + status + categories + lifecycle stage derivation; vendor list/detail UI.
- M3: RFQ create endpoints + line items begin.
- M4: Login/register UI wired; dashboard shell with placeholders.

### Hour 3: RFQ + Discovery

- M1: Seed data across lifecycle stages; Redis connection up.
- M2: Vendor discovery engine + lifecycle badges; discovery suggestions in invite list.
- M3: RFQ create UI, line item editor, vendor assignment, invites; activity logging on create/send.
- M4: Dashboard KPI cards wired to live counts.

### Hour 4: Quotation + Comparison (golden path must run here)

- M1: Ledger Merkle sealing + integrity endpoint.
- M2: Vendor portal RFQ list + quotation entry point.
- M3: Quotation draft/submit + GST calc + comparison API + lowest-price highlight + Best Value Score.
- M4: Comparison UI (table + radar/score bars), select-quote action.

### Hour 5: Approval + Risk

- M1: Redis caching for dashboard/report aggregates + login rate limiting.
- M2: Multi-criteria rating model (for later) + reputation scaffolding.
- M3: Procurement risk engine (Low/Med/High, 5 dimensions).
- M4: Approval list/detail UI, approve/reject, remarks, budget impact preview, risk + policy display.

### Hour 6: PO + Invoice + Delivery

- M1: Ledger UI (timeline + verify button) integration support.
- M2: PO vendor acceptance + delivery tracking (vendor portal).
- M3: Split procurement engine (P1-stretch) if ahead.
- M4: Generate PO + invoice, GST split, print/download/email outbox, 3-way match lite, buyer delivery view.

### Hour 7: Dashboard, Reports, Ledger, Notifications

- M1: Activity page + integrity verify finalized; notifications service.
- M2: Vendor growth analytics + reputation feedback loop (rating -> score -> stage).
- M3: Comparison/risk polish; partial fulfillment coverage display.
- M4: Reports/analytics + charts + CSV export; dashboard process map.

### Hour 8: Polish and Demo

- All: seed data final pass, UI consistency, error/empty/loading states, validation messages.
- M4: run end-to-end golden path twice; finalize 5-minute demo script; backup screenshots/video.
- M1: run backend tests + lint; confirm ledger triggers block edit/delete.
- All: assign presentation sections; final merge.

## 5. P0 Backlog

These are mandatory.

- [ ] Auth and roles.
- [ ] PostgreSQL schema and migrations.
- [ ] Seed data.
- [ ] Vendor management.
- [ ] RFQ creation.
- [ ] Vendor quotation submission.
- [ ] Quotation comparison.
- [ ] Approval workflow.
- [ ] PO generation.
- [ ] Invoice generation.
- [ ] Print/download/email action.
- [ ] Activity logs.
- [ ] Dashboard.
- [ ] Reports.
- [ ] Validation and error messages.
- [ ] Git workflow and README.

## 6. P1 Backlog

These are the winning differentiators.

Core:

- [ ] Blockchain-style ledger: hash chain + Merkle blocks + integrity verification.
- [ ] DB-level append-only protection (trigger) for ledger tables.
- [ ] Redis caching (analytics aggregates) + login rate limiting.
- [ ] Best Value Score + score breakdown UI.
- [ ] Budget Impact Preview.
- [ ] CGST/SGST vs IGST split.
- [ ] HSN/SAC validation.
- [ ] Vendor compliance badge.
- [ ] Vendor radar chart.
- [ ] 3-way match lite.
- [ ] ERP process map.

VendorBridge IQ intelligence layer:

- [ ] Vendor lifecycle (5 stages) + badges.
- [ ] Vendor reputation scores + multi-criteria ratings + feedback loop.
- [ ] Vendor discovery engine (fair RFQ distribution).
- [ ] Procurement risk engine (Low/Med/High, 5 dimensions).
- [ ] PO acceptance flow (accept/reject/request modification).
- [ ] Delivery tracking (packed -> shipped -> in transit -> delivered).
- [ ] Vendor growth analytics on dashboard/reports.

VendorBridge IQ high-complexity (P1-stretch, after the above):

- [ ] Partial fulfillment (available now / later).
- [ ] Split procurement engine + split PO/invoice numbering.

## 7. P2 Backlog

Stretch only.

- [ ] AI-generated comparison summary.
- [ ] OCR quote extraction.
- [ ] WhatsApp reminders.
- [ ] Reverse auction.
- [ ] Natural language search.
- [ ] WebSocket live notifications.
- [ ] Mobile swipe approval.
- [ ] External GSTN API.
- [ ] Multi-currency.
- [ ] Advanced supplier risk API.

## 8. Validation Tasks

Backend validation:

- [ ] Invalid email rejected.
- [ ] Weak password rejected.
- [ ] Duplicate email rejected.
- [ ] Invalid GSTIN rejected or flagged.
- [ ] Invalid PAN rejected or flagged.
- [ ] Invalid HSN/SAC rejected or flagged.
- [ ] RFQ deadline must be future.
- [ ] RFQ must have at least one line item before send.
- [ ] RFQ must have at least one vendor before send.
- [ ] Quantity must be positive.
- [ ] Unit price must be non-negative.
- [ ] Vendor cannot quote on unassigned RFQ.
- [ ] Vendor cannot edit submitted quotation after deadline.
- [ ] Reject approval requires remarks.
- [ ] Invalid state transitions are blocked.
- [ ] Vendor cannot view another vendor's quote.
- [ ] Activity log cannot be edited or deleted (API + DB trigger).
- [ ] Only assigned vendor can accept/reject a PO or update its delivery status.
- [ ] Rating values constrained to 1-5; only buyer of a delivered PO can rate.
- [ ] Partial fulfillment: available/additional quantities are non-negative and not greater than requested.
- [ ] Split allocation never exceeds requested quantity.
- [ ] Delivery and acceptance transitions follow the state machine.

Frontend validation:

- [ ] Inline error messages.
- [ ] Disabled submit for invalid forms.
- [ ] Toast on success/failure.
- [ ] Confirmation for sensitive actions.
- [ ] Empty states for empty lists.
- [ ] Loading states for API requests.

## 9. Test Tasks

Minimum tests:

- [ ] GSTIN validator unit test.
- [ ] PAN validator unit test.
- [ ] HSN/SAC validator unit test.
- [ ] Best Value Score unit test.
- [ ] Budget Impact Preview unit test.
- [ ] Approval routing unit test.
- [ ] Activity hash-chain unit test.
- [ ] RFQ create API test.
- [ ] Quotation submit API test.
- [ ] Approval approve/reject API test.
- [ ] Vendor authorization test.
- [ ] Vendor lifecycle stage derivation unit test.
- [ ] Reputation score computation unit test.
- [ ] Risk engine tier (Low/Med/High) unit test.
- [ ] Discovery engine fair-mix unit test.
- [ ] Merkle block sealing + integrity verification unit test.
- [ ] Split allocation engine unit test (partial fulfillment).

Manual smoke tests:

- [ ] Login as Admin.
- [ ] Login as Procurement Officer.
- [ ] Login as Vendor.
- [ ] Login as Manager.
- [ ] Create vendor.
- [ ] Create and send RFQ.
- [ ] Submit quotation.
- [ ] Compare quotation.
- [ ] Select quote.
- [ ] Approve request.
- [ ] Generate PO.
- [ ] Generate invoice.
- [ ] Download/print/email invoice.
- [ ] View activity logs.
- [ ] View reports.

## 10. Repository Insights To Reference During Build

Use these for implementation inspiration.

### Odoo Core

- [ ] `clones-odoo/odoo/addons/purchase/models/purchase_order.py`
  - RFQ/PO states.
  - `button_confirm`.
  - Invoice creation.
  - Portal and mail mixins.
- [ ] `clones-odoo/odoo/addons/purchase/controllers/portal.py`
  - Vendor portal route patterns.
- [ ] `clones-odoo/odoo/addons/account/models/account_move.py`
  - Invoice state, totals, and payment state.
- [ ] `clones-odoo/odoo/addons/account/wizard/account_move_send_wizard.py`
  - Send/download/print invoice flow.
- [ ] `clones-odoo/odoo/addons/mail/models/mail_thread.py`
  - Timeline/chatter inspiration.
- [ ] `clones-odoo/odoo/addons/base_vat/models/res_partner.py`
  - GSTIN validation inspiration.
- [ ] `clones-odoo/odoo/addons/l10n_in/models/res_partner.py`
  - GST treatment and PAN inspiration.
- [ ] `clones-odoo/odoo/addons/l10n_in/models/product_template.py`
  - HSN/SAC validation inspiration.
- [ ] `clones-odoo/odoo/addons/l10n_in_purchase/models/purchase_order.py`
  - GST treatment on purchase order inspiration.

### OCA Purchase Workflow

- [ ] `clones-odoo/purchase-workflow/purchase_request`
  - Internal request state machine.
- [ ] `clones-odoo/purchase-workflow/purchase_tier_validation`
  - Tier approval model.
- [ ] `clones-odoo/purchase-workflow/purchase_request_tier_validation`
  - Request approval tiering.
- [ ] `clones-odoo/purchase-workflow/purchase_order_approval_block`
  - Approval block reason pattern.
- [ ] `clones-odoo/purchase-workflow/purchase_exception`
  - Policy exception pattern.
- [ ] `clones-odoo/purchase-workflow/purchase_last_price_info`
  - Price history and savings anchor.
- [ ] `clones-odoo/purchase-workflow/purchase_reception_status`
  - Receiving status for 3-way match lite.

### ERPNext

- [ ] `clones-odoo/erpnext/erpnext/buying/doctype/request_for_quotation`
  - Supplier portal RFQ flow.
- [ ] `clones-odoo/erpnext/erpnext/buying/doctype/supplier_quotation`
  - Supplier quote model.
- [ ] `clones-odoo/erpnext/erpnext/buying/report/supplier_quotation_comparison`
  - Quote comparison report, minimum price, chart data.
- [ ] `clones-odoo/erpnext/erpnext/buying/doctype/supplier_scorecard`
  - Vendor scorecard.
- [ ] `clones-odoo/erpnext/erpnext/buying/doctype/supplier_scorecard_variable`
  - Metrics for on-time delivery, delayed shipments, received/rejected items, RFQ/SQ counts.

## 11. Demo Script Checklist

Use this exact story for judging.

- [ ] Start as Procurement Officer.
- [ ] Show dashboard KPIs and process map.
- [ ] Show vendors with lifecycle badges (Potential -> Preferred).
- [ ] Create "Office Furniture Procurement Q2" RFQ.
- [ ] Add items:
  - Ergonomic chair, 25 NOS.
  - Standing desk, 10 NOS.
- [ ] Use the discovery engine: show the fair mix of established + new vendors, then assign Infra Supplies, TechCore, OfficeNeed.
- [ ] Send RFQ.
- [ ] Switch to vendor account.
- [ ] Submit quotation with GST and payment terms (mention partial fulfillment if built).
- [ ] Switch back to Procurement Officer.
- [ ] Open comparison screen.
- [ ] Show lowest price highlight.
- [ ] Show Best Value Score + radar chart/score breakdown.
- [ ] Select winning quotation.
- [ ] Switch to Manager.
- [ ] Show the Low/Medium/High risk tier + breakdown.
- [ ] Show Budget Impact Preview + policy reasons.
- [ ] Approve with remarks.
- [ ] Generate PO.
- [ ] Switch to vendor: accept PO, advance delivery (packed -> shipped -> in transit -> delivered).
- [ ] Generate invoice; show CGST/SGST split.
- [ ] Download/print/email invoice.
- [ ] Rate the vendor (multi-criteria); show reputation/lifecycle update.
- [ ] Open reports (incl. vendor growth analytics).
- [ ] Open activity logs.
- [ ] End by showing the blockchain-style hash chain + Merkle blocks, click "Verify integrity" (PASS), and show there are no edit/delete controls and the DB rejects edits/deletes.

## 12. Presentation Ownership

Every team member should present a part because the video explicitly says teamwork matters.

Split (aligned to ownership in section 1.5):

- M1: Problem, product vision, database design, and the blockchain-style audit ledger (the closer).
- M2: Vendor marketplace - lifecycle, discovery engine, reputation.
- M3: Sourcing intelligence - RFQ, comparison, Best Value Score, risk engine (and split procurement if built).
- M4: Approvals, PO/invoice + GST, delivery tracking, reports, and the live demo run.

Each member presents their own vertical so ownership is visible to judges.

## 13. Git Workflow

Required because Odoo explicitly values team Git usage.

- [ ] Main branch protected by convention.
- [ ] Each teammate works on feature branches.
- [ ] Branch names:
  - `feature/auth`
  - `feature/vendors`
  - `feature/rfq`
  - `feature/quotations`
  - `feature/approvals`
  - `feature/invoices`
  - `feature/reports`
- [ ] Commit messages should be clear:
  - `feat: add RFQ creation API`
  - `fix: validate GSTIN before vendor save`
  - `test: cover approval routing`
- [ ] Pull before starting work.
- [ ] Do not commit `.env`, local DB files, generated junk, or cloned reference repos.
- [ ] Merge frequently to avoid last-hour integration failure.

## 14. Risk Register

### Risk: Building too many features

Impact: Core demo breaks.

Mitigation:

- Finish P0 before P1.
- Treat P2 as demo-only stretch.

### Risk: Weak database design

Impact: Fails one of Odoo's most important criteria.

Mitigation:

- Use PostgreSQL migrations.
- Show schema in presentation.
- Avoid static JSON.

### Risk: Overclaiming AI

Impact: Judges may ask how it works.

Mitigation:

- Call it Explainable Best Value Score.
- Show formula and component breakdown.

### Risk: PDF/email consumes too much time

Impact: PO/invoice flow slips.

Mitigation:

- First build print-friendly invoice page.
- Log email in `email_outbox`.
- Add actual PDF only if time remains.

### Risk: Odoo-native module takes too long

Impact: Team gets stuck in framework setup.

Mitigation:

- Use cloned Odoo repos as reference only.
- Build custom app unless rules require Odoo module.

### Risk: Immutable log implemented as normal timeline only

Impact: Misses hidden Excalidraw differentiator.

Mitigation:

- Create dedicated `activity_logs` table.
- No edit/delete controls.
- Add hash fields.
- Mention no soft-delete in demo.

### Risk: UI feels like isolated CRUD screens

Impact: Product seems shallow.

Mitigation:

- Use one connected demo flow.
- Show state transitions and generated downstream records.

## 15. Definition of Done

A feature is done only when:

- Database model exists.
- API endpoint exists.
- Backend validation exists.
- Frontend screen or action exists.
- Role permission is enforced.
- Activity log is written for important state changes.
- Success and failure feedback are visible.
- It works with seeded demo data.
- It does not rely on hardcoded JSON as final state.

## 16. Final Build Priority

The golden path (the demo spine) always comes first. If time is tight, build in this order:

Golden path (must always run end to end):

1. Database schema + seed data.
2. Auth and roles.
3. Vendor management.
4. RFQ creation.
5. Vendor quotation submission.
6. Quotation comparison (lowest-price highlight + Best Value Score).
7. Approval workflow (with risk tier + budget impact).
8. PO and invoice generation (GST split + print/download/email).
9. Blockchain-style activity ledger + live integrity verify (demo closer).

Then differentiators, in order:

10. Dashboard + reports.
11. Redis caching + rate limiting.
12. Vendor lifecycle + badges.
13. Vendor discovery engine.
14. Multi-criteria ratings + reputation feedback loop.
15. PO acceptance + delivery tracking.
16. GST polish (IGST path) + HSN/SAC.
17. 3-way match lite.
18. Radar chart + vendor growth analytics.

Last (P1-stretch, only if ahead):

19. Partial fulfillment.
20. Split procurement engine.

The app should be judged as a working, intelligent procurement ecosystem, not as a list of disconnected screens. Never sacrifice the golden path for a stretch feature.
