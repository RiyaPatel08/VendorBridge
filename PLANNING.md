# VendorBridge PLANNING.md

Last updated: 2026-06-06

This file is the high-level source of truth for Team BuzzBeatStrong's VendorBridge implementation during the Odoo hackathon. It captures the final hybrid proposal, architecture, scope boundaries, database plan, technical constraints, and the repository paths to study for implementation inspiration.

This version is finalized: the stack is locked, the database choice is decided (with alternatives evaluated and rejected), Redis caching and a blockchain-style immutable ledger are committed, and the expanded `VendorBridge IQ Overview.pdf` vision (vendor lifecycle, discovery engine, partial fulfillment, split procurement, risk engine, delivery tracking, reputation loop) has been folded into scope. Team is 4 people; ownership is in `TASK.md`.

## 0. Locked Decisions (read first)

These were open questions in earlier drafts. They are now decided. Do not re-litigate during the build.

- **Build type:** Custom full-stack app built from scratch. Not an Odoo-native module. Cloned repos in `clones-odoo/` are reference only.
- **Stack:** FastAPI + SQLAlchemy + Alembic + PostgreSQL (backend); React + TypeScript + Vite + Tailwind (frontend).
- **Primary database:** PostgreSQL as the single relational system-of-record. Alternatives evaluated and rejected (see §4).
- **Caching/perf:** Redis added as a scoped local cache + rate limiter (see §4 and §8).
- **Immutable audit log:** Implemented as a blockchain-style, hash-chained, Merkle-sealed, append-only ledger in PostgreSQL, with DB-level write protection and a live integrity-verification tool. No external/distributed blockchain (see §8).
- **Team:** 4 members. Roles and per-task ownership are defined in `TASK.md`.
- **Documents/email:** Print-friendly HTML invoice first, real PDF if time allows; email always written to an `email_outbox` table. Deployment optional (local is acceptable and preferred per criteria).
- **Scope posture:** Original 11 screens are the non-negotiable baseline. The `VendorBridge IQ` intelligence layer is the winning differentiator and is in scope because the team is 4 strong members using agentic tooling. Build order is still golden-path-first (see §3).

## 1. Product Decision

### Final Direction

Build VendorBridge as a source-to-pay procurement ERP for Indian SMEs and internal procurement teams.

The winning direction is a hybrid:

- Sonnet proposal as the execution scaffold: India context, 8-hour build plan, GST flows, role matrix, and practical screen coverage.
- Codex proposal as the technical backbone: immutable audit ledger, procurement state machines, data model depth, Odoo/OCA repo mapping, 3-way match lite, and Best Value Score.
- Arena proposal as UX enhancement source: Budget Impact Preview and vendor radar/comparison chart.
- Mentor review as the decision authority: prioritize database design, implementation feasibility, auditability, and India-native procurement details over flashy but fragile AI claims.

### Product Positioning

VendorBridge is a role-based procurement ERP that lets organizations create RFQs, invite vendors, receive quotations, compare best-value offers, run approval workflows, generate purchase orders and invoices, and preserve every procurement decision in a tamper-evident audit ledger.

### One-line Pitch

VendorBridge IQ turns procurement from scattered emails and manual approvals into an intelligent RFQ-to-invoice ecosystem: explainable best-value vendor selection, a fair vendor-discovery and reputation-growth marketplace, partial-fulfillment and split-procurement intelligence, budget-aware risk-scored approvals, India-ready GST handling, and a blockchain-style immutable audit ledger.

### Intelligence Layer (from VendorBridge IQ Overview)

On top of the baseline ERP workflow, VendorBridge IQ adds the decision-support layer that separates it from a CRUD app:

- **Vendor growth lifecycle:** Potential -> Emerging -> Verified -> Trusted -> Preferred, derived from completed-order history.
- **Vendor discovery engine:** Fairly distributes RFQ invitations across a mix of established and new vendors so new vendors get opportunities.
- **Partial fulfillment:** Vendors can offer part of the quantity now and the rest later, instead of being excluded.
- **Split procurement engine:** When no single vendor can fulfill demand, the system recommends splitting the order across vendors with split PO numbering (e.g. PO-2026-0001A / -0001B).
- **Procurement risk engine:** Low / Medium / High risk tiers computed from verification, delivery reliability, inventory availability, vendor history, and price abnormality, shown to the manager before approval.
- **Delivery tracking + PO acceptance:** Vendors accept/reject/request-modification on a PO, then update Packed -> Shipped -> In Transit -> Delivered.
- **Reputation feedback loop:** Multi-criteria post-delivery ratings (quality, delivery speed, communication, service) feed reliability/delivery/completion/satisfaction scores and advance the vendor's lifecycle stage.

### Demo Promise

In the demo, the team should prove one complete procurement story:

1. Procurement Officer creates an RFQ.
2. Vendors submit quotations.
3. Procurement team compares quotes using price, delivery, rating, compliance, and payment terms.
4. Manager sees budget impact and policy reasons before approval.
5. Approved quotation becomes a purchase order and invoice.
6. Invoice can be downloaded, printed, and "emailed" through a logged outbox.
7. Every critical event appears in an immutable audit ledger with hash-chain proof.

## 2. Ground Truth Sources

### Provided Problem Statement

File:

- `Vendorbridge Hackathon Problem Statement.pdf`

Core requirements:

- Login/signup with validation, forgot password, sessions, and role-based access.
- Dashboard with pending approvals, active RFQs, recent POs, recent invoices, analytics cards, and quick actions.
- Vendor management with vendor registration, vendor status, categories, GST details, contact details, search, and filtering.
- RFQ creation with title, product/service details, quantities, attachments, deadline, and vendor assignment.
- Vendor quotation submission with pricing, delivery timelines, notes/comments, editable quotations, and final submission.
- Quotation comparison with side-by-side comparison, lowest-price highlighting, delivery comparison, vendor rating indicators, sorting, and filtering.
- Approval workflow with approve/reject actions, remarks, timeline, status tracking, and workflow state transitions.
- Purchase order and invoice generation with auto PO number, tax calculations, total calculations, invoice PDF download, print, email, and status updates.
- Activity logs and notifications for RFQs, approvals, invoices, activity timeline, and audit logs.
- Reports and analytics with vendor performance, procurement statistics, spending summaries, monthly trends, and exportable reports.

### Expanded Vision: VendorBridge IQ Overview

File:

- `VendorBridge IQ Overview.pdf`

This is the expanded "intelligent procurement ecosystem" brief. It keeps everything in the base problem statement and adds a decision-support and marketplace layer. The base 11 screens remain mandatory; the IQ concepts below are the differentiators we deliberately adopt:

- Vendor growth lifecycle in 5 stages (Potential, Emerging, Verified, Trusted, Preferred) based on successful-order count.
- Vendor discovery engine that fairly mixes established and new vendors when distributing RFQs.
- Vendor inventory declaration and partial fulfillment (available now vs available later).
- Intelligent quotation comparison across price, quantity availability, delivery, vendor maturity, and past performance.
- Split procurement engine with split PO numbering when one vendor cannot fully satisfy demand.
- Procurement risk analysis with Low/Medium/High tiers across 5 dimensions, surfaced before approval.
- PO acceptance flow (accept / reject / request modification) and delivery tracking (Packed -> Shipped -> In Transit -> Delivered).
- Post-delivery multi-criteria vendor rating feeding a reputation score and lifecycle progression.
- Procurement intelligence dashboard with vendor growth and emerging-vendor analytics.

Decision: treat the IQ Overview as authoritative expanded scope. Adopt the high-ROI intelligence features as P1 differentiators, keep the base screens as P0, and never let IQ features block the golden path.

### Provided Excalidraw

File:

- `VendorBridge - 8 hours.excalidraw`

Important screen details:

- Screen 1: Login.
- Screen 2: Registration with first name, last name, email, phone, role, country, and additional information.
- Screen 3: Dashboard with active RFQs, pending approvals, POs this month, overdue invoices, spending trend, recent POs, and quick actions.
- Screen 4: Vendors page with GST number, category, contact number, status, search, and filters for all/active/pending/blocked.
- Screen 5: RFQ creation with title, category, deadline, description, line items, assigned vendors, attachments, save/send, and draft behavior.
- Screen 6: Vendor quotation submission with item prices, delivery days, GST percent, terms, subtotal, GST, grand total, submit, and save draft.
- Screen 7: Quotation comparison with grand total, GST, delivery days, vendor rating, payment terms, lowest-price highlight, and select/approve.
- Screen 8: Approval workflow with submitted, L1 review, L2 approval, generate PO, remarks, quotation summary, approve, and reject.
- Screen 9: Purchase order and invoice with PO number, invoice date, due date, vendor/bill-to GSTIN, CGST, SGST, grand total, download PDF, print, and email invoice.
- Screen 10: Activity and logs page. Critical note: "Audit logs must be immutable. These entries must be write-once, no edit or delete. Make sure your DB schema reflects this (no soft-delete on log records)."
- Screen 11: Reports and analytics page with vendor performance, procurement statistics, spend summaries, monthly trends, and overdue invoice insight.

### Mentor Review

File:

- `mentor-final-proposal-review.md`

Key decisions from mentor:

- No single proposal wins. The correct path is a hybrid.
- Keep Sonnet's 8-hour execution plan and India-specific GST intelligence.
- Add Codex's immutable ledger, data model/state machines, OCA references, 3-way match lite, and Best Value Score.
- Add Arena's Budget Impact Preview and vendor radar chart.
- Avoid overbuilding natural language search, swipe-to-approve, reverse auction, full OCR, WhatsApp, or real AI unless the core is already complete.

### Instructional Video Transcript

Odoo's hiring hackathon guidance strongly affects the technical plan:

- Database design matters most.
- Prefer local relational databases such as PostgreSQL or MySQL.
- Do not rely heavily on Firebase, Supabase, MongoDB Atlas, or Backend-as-a-Service platforms.
- Static JSON is acceptable only for quick prototypes, not final solution state.
- Build from scratch with minimal third-party API dependency.
- Validate inputs robustly and handle user errors gracefully.
- Use Git as a team, not as one person's responsibility.
- UI must be clean, consistent, interactive, and intuitive.
- Technologies like AI, blockchain, or chatbots are good only if they genuinely add value and the team understands them.
- Evaluation focuses on coding standards, logic, modularity, frontend design, performance, scalability, security, usability, debugging, database design, approach, architecture, coding patterns, and attention to detail.

## 3. Scope Strategy

### Golden Path (the demo spine — must always work)

Even with 4 strong members, protect one connected vertical slice above everything else. If anything is at risk, this is what must run end to end:

1. Login as Procurement Officer, Vendor, and Manager (auth + roles).
2. Officer creates the RFQ (2 line items) and assigns vendors.
3. Vendor logs in, submits a quotation with GST.
4. Officer opens comparison: lowest price highlighted (literal requirement) + Best Value Score.
5. Officer selects a quote -> approval initiated.
6. Manager sees risk tier + budget impact, approves with remarks.
7. PO generated -> invoice generated with CGST/SGST split.
8. Invoice download/print + email-to-outbox, each action logged.
9. Activity page shows the blockchain-style immutable, hash-linked ledger with a live "verify integrity" check and no edit/delete. (Demo closer.)

Build vertical slices (backend + clean validated UI together). The demo must be runnable end to end by the end of every hour from Hour 4 onward.

### P0: Must Ship

P0 is the minimum complete product. Do not polish P1 features until P0 works end to end.

- Authentication and roles: Admin, Procurement Officer, Vendor, Manager/Approver.
- Dashboard with live database counts and quick actions.
- Vendor CRUD with GSTIN, PAN, category, status, contact details, search, and filters.
- RFQ creation with line items, deadline, category, vendor assignment, attachment placeholder, save draft, and send.
- Vendor quotation submission with editable draft before deadline.
- Quotation comparison table with lowest-price highlight and sorting/filtering.
- Select quotation and initiate approval.
- Approval workflow with approve/reject, remarks, timeline, and status transition.
- Generate PO from approved quotation.
- Generate invoice from PO with subtotal, GST, grand total, PDF/download/print/email action buttons.
- Activity log and notification feed.
- Reports page with at least 4 KPIs, spend summary, vendor performance, and CSV export.
- Seed data for a smooth demo.

### P1: Winning Layer

These features differentiate the project while remaining feasible. Build them after the golden path is solid. They split into the "core differentiators" and the "VendorBridge IQ intelligence layer".

Core differentiators:

- Explainable Best Value Score.
- Blockchain-style immutable audit ledger: hash chain (`previous_hash` + `entry_hash`), periodic Merkle block sealing, DB-level append-only enforcement, and a live integrity-verification tool.
- Redis caching for analytics/dashboard aggregates + login rate limiting.
- Budget Impact Preview on approval screen.
- India-native GST split: intra-state CGST+SGST, inter-state IGST.
- HSN/SAC field and validation.
- Vendor compliance badge.
- 3-way match lite before invoice is marked payable/paid.
- ERP process map on dashboard: RFQ -> Quotes -> Approval -> PO -> Invoice -> Paid.
- Vendor radar chart or score bars on comparison screen.

VendorBridge IQ intelligence layer (adopted from `VendorBridge IQ Overview.pdf`):

- Vendor growth lifecycle (5 stages) with badge, derived from completed orders.
- Vendor discovery engine: fair RFQ distribution across a mix of established and new vendors.
- Procurement risk engine: Low/Medium/High tiers across 5 dimensions, shown on the approval/risk screen (this upgrades the policy-reason badges into a named risk score).
- Multi-criteria vendor rating (quality, delivery speed, communication, service) feeding reputation scores and lifecycle progression.
- PO acceptance flow (accept / reject / request modification).
- Delivery tracking state machine: Packed -> Shipped -> In Transit -> Delivered.

VendorBridge IQ high-complexity (P1-stretch — build only after the above and the golden path are stable):

- Partial fulfillment: vendor offers part now, rest later (schema + comparison support).
- Split procurement engine: allocate one RFQ across multiple vendors with split PO numbering (PO-...A / PO-...B) and split invoices.

### P2: Stretch Only

Only attempt after P0 and P1 are stable.

- AI-generated comparison summary.
- OCR/PDF quote extraction.
- WhatsApp reminders.
- Reverse auction.
- Natural language search.
- Real-time WebSocket collaboration.
- Full mobile swipe-to-approve UI.
- External GSTN/e-invoice/e-way bill integrations.
- Multi-currency procurement.
- Advanced supplier risk API.

### Explicit Non-goals

- Do not modify the cloned Odoo/OCA/ERPNext repositories directly.
- Do not build a full Odoo module unless the hackathon rules explicitly require it or the team is already comfortable with Odoo development.
- Do not rely on static JSON as the final data source.
- Do not use Firebase/Supabase as the system of record.
- Do not call features "AI" unless they use an actual model. Weighted scoring should be called "Explainable Best Value Score".
- Do not attempt full statutory GST compliance. Implement a demo-grade GST workflow inspired by Odoo's Indian localization patterns.

## 4. Locked Tech Stack

This is decided. The stack below is frozen for the build.

Backend:

- Python FastAPI.
- SQLAlchemy ORM.
- Alembic migrations.
- Pydantic request/response validation.
- PostgreSQL local database (single system-of-record).
- Redis (local) for caching + rate limiting.
- JWT or signed cookie sessions.
- Argon2 or bcrypt password hashing.
- Pytest for service and API tests.

Frontend:

- React + TypeScript.
- Vite.
- Tailwind CSS.
- shadcn/ui or Radix primitives where useful.
- Recharts for charts and radar chart.
- Zod or React Hook Form validation on the client.

Supporting tools:

- Docker Compose for local PostgreSQL + Redis.
- Local file storage for attachments.
- HTML/CSS print view for invoices first; PDF generation second.
- SMTP/email simulated through an `email_outbox` table unless real email is easy and reliable.

### Why PostgreSQL (and why not the alternatives)

The instructional video and the official hackathon criteria explicitly reward local relational databases (PostgreSQL/MySQL), building from scratch, and avoiding Backend-as-a-Service. Database design is the single most-weighted criterion, and "database design" here means relational modeling, constraints, and query design. We evaluated the experimental alternatives and rejected them:

- **PostgreSQL (chosen):** Mature, ACID, relational, what Odoo itself runs on. Judges are Odoo engineers; using Postgres signals competence and lets the schema be the star. Lowest risk, highest signal. Performance comes from good indexing, materialized views for analytics, JSONB where useful, connection pooling, and Redis caching, not from an exotic engine.
- **SpacetimeDB (rejected):** In-memory database with a single global mutex that serializes all reads and writes; not distributed (vertical scaling only); entire dataset must fit in RAM; asynchronous WAL flushing with documented durability/corruption risk; application logic runs as WASM modules inside the DB (steep learning curve); its production path is the managed Maincloud (a cloud/BaaS), which violates the "local, from-scratch, no-cloud" guidance. It is purpose-built for real-time games and "overkill for standard CRUD apps." Using it would burn learning time, risk the demo, and contradict the stated criteria.
- **DuckDB (rejected as primary):** In-process OLAP engine, single-writer across processes; DuckDB's own maintainers advise using Postgres for a webserver backend. It is not a transactional multi-user system-of-record. It could be an optional read-only analytics sidecar for the reports page, but that is not worth the integration cost in this time box.
- **Convex (rejected):** A hosted Backend-as-a-Service. The criteria explicitly say to avoid BaaS (Firebase, Supabase, MongoDB Atlas, etc.). Disqualified by the rules.

Net: PostgreSQL is both the safe choice and the choice the judges actually reward. Differentiation comes from schema quality, the blockchain-style ledger, and the IQ intelligence layer, not from a trendy database.

### Why Redis (used deliberately, not decoratively)

Redis is added because it maps cleanly to the "performance / scalability" evaluation criteria and is defensible under questioning, and because it runs locally (no cloud dependency). Scoped uses only:

- Cache-aside for expensive dashboard/report aggregates, with explicit invalidation on writes that affect them.
- Login rate limiting (brute-force protection).
- Optional session storage and caching of vendor reputation/lifecycle computations.

Rule: every Redis use must have correct invalidation and a clear reason. Build it after the golden path works. Do not sprinkle caching where it adds no value.

### Why a blockchain-style ledger (not a real blockchain)

The Excalidraw mandates write-once, no-edit, no-delete, no-soft-delete audit logs, and the criteria encourage trendy tech (e.g. blockchain) only when it adds real value and the team understands it. We satisfy both by implementing the cryptographic core of a blockchain locally in PostgreSQL (hash chain + Merkle sealing + integrity verification + DB-enforced append-only). We deliberately do not use an external/distributed chain (Ethereum, Hyperledger, consensus, gas, nodes): distributed consensus adds no value for a single-organization audit log, would need network/cloud, and would invite the fair question "why do you need consensus here?". Details in §8.

## 5. Architecture

### High-level Architecture

```text
Browser UI
  |
  | REST/JSON API
  v
Backend API
  - Auth module
  - Vendor module
  - RFQ module
  - Quotation module
  - Approval module
  - PO module
  - Invoice module
  - Activity ledger module
  - Reports module
  |
  | SQLAlchemy/Prisma
  v
PostgreSQL
  - Relational business data
  - Immutable activity log
  - Email outbox
  - Seed/demo data
```

### Module Boundaries

Backend modules:

- `auth`: login, signup, forgot password placeholder, sessions, password hashing, RBAC.
- `users`: user profiles, roles, admin management.
- `vendors`: vendor registration, GST/PAN validation, categories, status, lifecycle stage, reputation scores, multi-criteria ratings.
- `discovery`: vendor discovery engine (fair RFQ distribution across lifecycle stages).
- `rfqs`: RFQ creation, line items, assigned vendors, deadlines, attachments.
- `quotations`: vendor drafts, final submission, quote lines, totals, partial-fulfillment fields, deadline guard.
- `comparison`: lowest price, best value score, coverage/availability, radar metrics, sorting/filtering.
- `risk`: procurement risk engine (Low/Medium/High across 5 dimensions).
- `approvals`: approval request, approval steps, remarks, policy reasons, risk tier, budget impact.
- `purchase_orders`: PO generation (incl. split POs), vendor acceptance, line copy from selected quotation, status changes.
- `split_procurement`: allocation across vendors and split PO/invoice generation (P1-stretch).
- `deliveries`: PO delivery tracking state machine and buyer receipt confirmation.
- `invoices`: invoice generation, GST totals, print/download/email action logging, payment status.
- `budgets`: department/category budget tracking and remaining budget calculations.
- `activity_logs`: blockchain-style append-only ledger (hash chain + Merkle blocks + integrity verification) and notifications.
- `reports`: spend summaries, vendor performance, vendor growth analytics, procurement stats, exports.
- `cache`: Redis cache-aside helpers and invalidation hooks (cross-cutting).

Frontend modules/pages:

- `/login`
- `/register`
- `/dashboard`
- `/vendors`
- `/vendors/:id`
- `/rfqs`
- `/rfqs/new`
- `/rfqs/:id`
- `/vendor/rfqs`
- `/vendor/rfqs/:id/quote`
- `/quotations/:rfqId/compare`
- `/approvals`
- `/approvals/:id`
- `/purchase-orders`
- `/purchase-orders/:id`
- `/invoices`
- `/invoices/:id`
- `/activity`
- `/reports`

## 6. Database Design

The database is the center of the project. It must be relational, normalized enough to show ERP thinking, and backed by migrations.

### Core Tables

#### `users`

- `id`
- `first_name`
- `last_name`
- `email` unique
- `phone`
- `password_hash`
- `role` enum: `admin`, `procurement_officer`, `vendor`, `manager`
- `department`
- `country`
- `is_active`
- `created_at`
- `updated_at`

#### `vendors`

- `id`
- `company_name`
- `contact_person`
- `email`
- `phone`
- `address_line1`
- `city`
- `state`
- `country`
- `gstin`
- `pan`
- `category_id`
- `status` enum: `pending`, `active`, `blocked`, `inactive`
- `rating` (overall average, derived from `vendor_ratings`)
- `lifecycle_stage` enum: `potential`, `emerging`, `verified`, `trusted`, `preferred` (derived from `completed_orders_count`)
- `completed_orders_count`
- `reliability_score`
- `delivery_score`
- `completion_rate`
- `satisfaction_score`
- `reputation_score` (composite used by discovery + comparison)
- `gst_verified`
- `email_verified`
- `phone_verified`
- `payment_terms_days`
- `bank_name`
- `bank_account_masked`
- `created_by`
- `created_at`
- `updated_at`

Lifecycle thresholds (by `completed_orders_count`): `potential` = 0, `emerging` = 1-4, `verified` = 5-19, `trusted` = 20-99, `preferred` = 100+. Stage is recomputed when an order completes and the change is written to the activity ledger.

#### `vendor_ratings`

Post-delivery multi-criteria ratings. Feeds reputation scores and lifecycle progression.

- `id`
- `vendor_id`
- `purchase_order_id`
- `rated_by`
- `product_quality` (1-5)
- `delivery_speed` (1-5)
- `communication` (1-5)
- `service_experience` (1-5)
- `comment`
- `created_at`

#### `vendor_categories`

- `id`
- `name`
- `description`

#### `rfqs`

- `id`
- `rfq_number` unique, format example: `RFQ-2026-0001`
- `title`
- `description`
- `category_id`
- `created_by`
- `deadline`
- `status` enum: `draft`, `sent`, `quotes_received`, `comparison`, `approval_pending`, `approved`, `po_generated`, `closed`, `cancelled`
- `selected_quotation_id` nullable
- `created_at`
- `updated_at`

#### `rfq_items`

- `id`
- `rfq_id`
- `item_name`
- `description`
- `quantity`
- `unit`
- `hsn_sac_code`
- `estimated_unit_price`
- `created_at`

#### `rfq_vendor_invites`

- `id`
- `rfq_id`
- `vendor_id`
- `invite_token`
- `status` enum: `invited`, `viewed`, `draft_quote`, `submitted`, `declined`, `expired`
- `discovery_source` enum: `manual`, `established`, `new_opportunity` (records why the discovery engine included this vendor; supports the fair-distribution story)
- `vendor_lifecycle_stage_at_invite` (snapshot for fairness reporting)
- `sent_at`
- `viewed_at`
- `submitted_at`

#### `quotations`

- `id`
- `quotation_number`
- `rfq_id`
- `vendor_id`
- `status` enum: `draft`, `submitted`, `revised`, `selected`, `rejected`, `expired`
- `delivery_days`
- `payment_terms_days`
- `notes`
- `subtotal`
- `gst_rate`
- `cgst_amount`
- `sgst_amount`
- `igst_amount`
- `grand_total`
- `best_value_score`
- `submitted_at`
- `created_at`
- `updated_at`

#### `quotation_items`

- `id`
- `quotation_id`
- `rfq_item_id`
- `unit_price`
- `quantity` (requested quantity reference)
- `available_quantity` (quantity the vendor can fulfill now — supports partial fulfillment)
- `additional_quantity` (extra quantity available later)
- `additional_available_days` (lead time for the additional quantity)
- `line_subtotal`
- `gst_rate`
- `line_total`

#### `approval_requests`

- `id`
- `rfq_id`
- `quotation_id`
- `requested_by`
- `current_step`
- `status` enum: `pending`, `approved`, `rejected`, `needs_revision`, `cancelled`
- `policy_reasons` JSON or text array
- `risk_level` enum: `low`, `medium`, `high`
- `risk_score`
- `risk_breakdown` JSON (per-dimension scores: verification, delivery reliability, inventory availability, vendor history, price abnormality)
- `budget_id`
- `budget_before`
- `budget_after`
- `created_at`
- `updated_at`

#### `approval_steps`

- `id`
- `approval_request_id`
- `level`
- `approver_id`
- `status` enum: `pending`, `approved`, `rejected`, `skipped`
- `remarks`
- `assigned_at`
- `decided_at`

#### `budgets`

- `id`
- `department`
- `category_id`
- `fiscal_year`
- `allocated_amount`
- `spent_amount`
- `reserved_amount`
- `created_at`
- `updated_at`

#### `purchase_orders`

- `id`
- `po_number` unique, format example: `PO-2026-0001` (split POs use a suffix, e.g. `PO-2026-0001A`)
- `rfq_id`
- `quotation_id`
- `vendor_id`
- `status` enum: `draft`, `generated`, `sent`, `accepted`, `received`, `invoiced`, `closed`, `cancelled`
- `split_group_id` nullable (groups the POs that together fulfill one RFQ)
- `split_label` nullable (e.g. `A`, `B` for split procurement)
- `vendor_acceptance_status` enum: `pending`, `accepted`, `rejected`, `modification_requested`
- `vendor_acceptance_note`
- `delivery_status` enum: `not_started`, `packed`, `shipped`, `in_transit`, `delivered`
- `subtotal`
- `cgst_amount`
- `sgst_amount`
- `igst_amount`
- `grand_total`
- `po_date`
- `expected_delivery_date`
- `delivered_at`
- `created_at`
- `updated_at`

#### `purchase_order_items`

- `id`
- `purchase_order_id`
- `item_name`
- `quantity`
- `unit`
- `unit_price`
- `hsn_sac_code`
- `received_quantity`
- `accepted_quantity`
- `line_total`

#### `invoices`

- `id`
- `invoice_number` unique, format example: `INV-2026-0001`
- `purchase_order_id`
- `vendor_id`
- `status` enum: `draft`, `generated`, `sent`, `payable`, `paid`, `overdue`, `cancelled`
- `invoice_date`
- `due_date`
- `subtotal`
- `cgst_amount`
- `sgst_amount`
- `igst_amount`
- `grand_total`
- `emailed_at`
- `paid_at`
- `created_at`
- `updated_at`

#### `invoice_items`

- `id`
- `invoice_id`
- `purchase_order_item_id`
- `item_name`
- `quantity`
- `unit_price`
- `line_total`

#### `activity_logs`

This table is special. It must be append-only.

- `id`
- `sequence_number` unique and increasing
- `actor_user_id`
- `actor_role`
- `event_type`
- `entity_type`
- `entity_id`
- `event_summary`
- `event_payload` JSON/text
- `ip_address`
- `user_agent`
- `previous_hash`
- `entry_hash`
- `block_id` nullable (set when the entry is sealed into a Merkle block)
- `signature` nullable (optional server signature over `entry_hash`)
- `created_at`

Rules:

- No `updated_at`.
- No `deleted_at`.
- No update endpoint.
- No delete endpoint.
- Add a database trigger to reject UPDATE and DELETE (this is committed, not "if time permits" — it is the literal Excalidraw requirement).
- Each `entry_hash` is computed from canonical event fields plus `previous_hash` (the hash chain).

#### `activity_log_blocks`

Periodic Merkle-sealed blocks over ranges of `activity_logs` entries. This is the "blockchain" structure that makes the ledger tamper-evident and efficiently verifiable.

- `id`
- `block_number` unique and increasing
- `from_sequence_number`
- `to_sequence_number`
- `merkle_root`
- `previous_block_hash`
- `block_hash`
- `signature` nullable (optional server signature over `block_hash`)
- `entry_count`
- `sealed_at`

Rules:

- Append-only, same UPDATE/DELETE protection as `activity_logs`.
- A block seals when N entries accumulate or on demand (e.g. at the end of the demo).
- The integrity-verification tool recomputes the entry hash chain and the Merkle roots and confirms each block links to the previous block.

#### `notifications`

- `id`
- `user_id`
- `type`
- `title`
- `message`
- `entity_type`
- `entity_id`
- `read_at`
- `created_at`

#### `email_outbox`

- `id`
- `to_email`
- `subject`
- `body`
- `entity_type`
- `entity_id`
- `status` enum: `queued`, `sent`, `failed`
- `sent_at`
- `created_at`

### Useful Indexes

- `users.email`
- `vendors.gstin`
- `vendors.category_id`
- `vendors.status`
- `rfqs.status`
- `rfqs.deadline`
- `rfq_vendor_invites.rfq_id`
- `rfq_vendor_invites.vendor_id`
- `quotations.rfq_id`
- `quotations.vendor_id`
- `approval_requests.status`
- `purchase_orders.po_number`
- `invoices.invoice_number`
- `activity_logs.sequence_number`
- `activity_logs.entity_type, entity_id`
- `notifications.user_id, read_at`

## 7. State Machines

### RFQ

```text
draft -> sent -> quotes_received -> comparison -> approval_pending -> approved -> po_generated -> closed
draft -> cancelled
sent -> cancelled
approval_pending -> comparison
approval_pending -> cancelled
```

### Quotation

```text
draft -> submitted -> revised
submitted -> selected
submitted -> rejected
submitted -> expired
```

Rules:

- Vendor can edit only while quotation is `draft` or before RFQ deadline.
- Submitted quotations should not be silently changed. Revisions should create a logged event.

### Approval

```text
pending -> approved
pending -> rejected
pending -> needs_revision
needs_revision -> pending
```

Rules:

- Reject requires remarks.
- Approval must record approver, timestamp, and policy context.
- Above threshold approvals require L1 and L2 steps.

### Purchase Order

```text
draft -> generated -> sent -> accepted -> received -> invoiced -> closed
generated -> cancelled
sent -> cancelled
```

Vendor acceptance (`vendor_acceptance_status`), runs after the PO is `sent`:

```text
pending -> accepted
pending -> rejected
pending -> modification_requested -> (officer revises) -> pending
```

Delivery tracking (`delivery_status`), runs after acceptance:

```text
not_started -> packed -> shipped -> in_transit -> delivered
```

Rules:

- Only the assigned vendor can update acceptance and delivery status.
- `received` (PO status) is set when `delivery_status` reaches `delivered` and the buyer confirms receipt.
- Split POs each run their own acceptance and delivery state independently under a shared `split_group_id`.

### Invoice

```text
draft -> generated -> sent -> payable -> paid
sent -> overdue
generated -> cancelled
```

Rules:

- Invoice can be `payable` only after 3-way match lite passes.
- Payment status changes must be logged.

## 8. Business Logic

### Best Value Score

Use explainable weighted scoring, not vague AI.

Suggested formula:

```text
best_value_score =
  price_score * 0.40 +
  delivery_score * 0.20 +
  vendor_rating_score * 0.15 +
  compliance_score * 0.15 +
  payment_terms_score * 0.10
```

Score components:

- `price_score`: best/lowest quotation gets 100; others scale down relative to lowest.
- `delivery_score`: shorter delivery gets higher score.
- `vendor_rating_score`: use vendor rating out of 5 converted to 100.
- `compliance_score`: GSTIN valid, PAN present, vendor active, no blocked status.
- `payment_terms_score`: longer payment terms are better for buyer cash flow.

Display:

- Final score.
- Breakdown bar or mini table.
- Reason text: "Recommended because price is competitive, vendor rating is high, and GST details are valid."

### Budget Impact Preview

Approval page should show:

```text
Department budget: INR 5,00,000
Already spent: INR 80,000
This PO: INR 2,00,010
Remaining after approval: INR 2,19,990
Budget health: Green / Yellow / Red
```

Color rules:

- Green: after approval >= 25 percent of budget remains.
- Yellow: after approval between 0 and 25 percent remains.
- Red: approval exceeds remaining budget.

### GST Logic

Demo-grade India GST support:

- Validate GSTIN format using regex inspired by Odoo `base_vat` and `l10n_in`.
- Validate PAN format where captured.
- Validate HSN/SAC as 4, 6, or 8 digits.
- If vendor state equals company state, split GST as CGST + SGST.
- If vendor state differs from company state, use IGST.
- Default GST rate for demo: 18 percent.
- Do not call external GSTN APIs.

### Approval Policy

Initial threshold rules:

- Less than INR 50,000: auto-approval or single L1 approval depending on demo confidence.
- INR 50,000 to INR 2,00,000: L1 Manager approval.
- Greater than INR 2,00,000: L1 Procurement Head plus L2 Finance Manager.

Additional policy reasons:

- Vendor is pending or blocked.
- GSTIN missing or invalid.
- Only one quotation received.
- Best Value Score below threshold.
- Budget impact is yellow or red.
- Selected vendor is not lowest price.

### 3-way Match Lite

Before invoice becomes payable:

- PO quantity.
- Received quantity.
- Accepted quantity.
- Invoice quantity.
- PO amount vs invoice amount.

Demo behavior:

- Show a simple match card.
- If accepted quantity equals invoice quantity and invoice amount equals PO amount, mark as matched.
- If not, show warning and require manager override or block payable status.

### Vendor Lifecycle and Reputation

Each vendor has a `lifecycle_stage` derived from `completed_orders_count`:

- `potential` = 0 completed orders (newly registered, identity verified, no performance data).
- `emerging` = 1-4.
- `verified` = 5-19.
- `trusted` = 20-99.
- `preferred` = 100+.

Reputation scores are computed from `vendor_ratings` (post-delivery, 4 criteria each 1-5):

- `reliability_score`, `delivery_score`, `completion_rate`, `satisfaction_score`, and a composite `reputation_score`.
- When an order completes and is rated, recompute the scores, recompute `lifecycle_stage`, and write a ledger event if the stage changes.
- Seed vendors across multiple stages so the demo shows the full ladder immediately.

### Vendor Discovery Engine

When the officer builds an RFQ invite list, the engine recommends a fair mix instead of only established vendors:

- Default suggestion: a configurable mix (for the demo, e.g. 3 established + 2 new) drawn by `lifecycle_stage`.
- Established = `verified`/`trusted`/`preferred`; new = `potential`/`emerging` (filtered by matching category and active status).
- Record `discovery_source` and `vendor_lifecycle_stage_at_invite` on each invite to evidence the fairness story.
- The officer can still manually add/remove vendors; the engine only suggests.

### Procurement Risk Engine

Upgrades the policy-reason badges into a named Low/Medium/High risk score shown to the manager before approval. Evaluate 5 dimensions and store the breakdown in `approval_requests.risk_breakdown`:

- Vendor verification (GSTIN/PAN/email/phone verified, not blocked).
- Delivery reliability (delivery score / on-time history).
- Inventory availability (can the chosen quote(s) fully cover the requirement?).
- Vendor history (lifecycle stage / completed orders).
- Price abnormality (selected price vs lowest/average quote; flag unusually high or suspiciously low).

Map the weighted result to `low` / `medium` / `high`. Keep the existing policy reasons as the human-readable explanation under the risk tier.

### Partial Fulfillment (P1-stretch)

Vendors may offer part of the quantity now and the rest later via `available_quantity`, `additional_quantity`, and `additional_available_days` on quotation items.

- Comparison shows coverage (e.g. "15 of 20 now, 5 in 7 days").
- A quote that cannot fully cover the requirement is not auto-excluded; it becomes a candidate for split procurement.

### Split Procurement Engine (P1-stretch)

When no single vendor fully covers the requirement, recommend an allocation across vendors.

- Greedy allocation: fill from the best-value / most-available vendors until the requested quantity is met.
- Generate one PO per vendor sharing a `split_group_id`, with `split_label` `A`, `B`, ... and PO numbers `PO-2026-0001A`, `PO-2026-0001B`.
- Each split PO produces its own invoice and its own delivery tracking.
- Build this only after the golden path, lifecycle, discovery, risk, and delivery features are stable. It is the flashiest feature but also the most complex; do not let it endanger the core demo.

### Blockchain-style Immutable Ledger

This is the implementation of the Excalidraw immutable-log requirement and the "use blockchain meaningfully" criterion, built from scratch in PostgreSQL.

- **Hash chain:** each `activity_logs` row stores `previous_hash` and `entry_hash = hash(canonical_fields || previous_hash)`.
- **Merkle blocks:** every N entries (and on demand at demo end), seal a block in `activity_log_blocks` with a `merkle_root` over the entries and `block_hash` linking to `previous_block_hash`.
- **Append-only enforcement:** no update/delete endpoints, no soft-delete columns, plus a DB trigger that rejects UPDATE and DELETE on both ledger tables.
- **Optional signatures:** sign `entry_hash`/`block_hash` with a server keypair for authenticity.
- **Integrity verification tool:** an endpoint + UI button that recomputes the entire chain and all Merkle roots and reports PASS/FAIL, demonstrating tamper-evidence live.
- **Framing:** present this honestly as a "blockchain-inspired / cryptographically verifiable ledger". Do not claim distributed consensus. If asked "why not a real blockchain", the answer is: distributed consensus adds no value for a single-organization audit log and would require network/cloud, violating the from-scratch/local constraint.

## 9. Security and Validation

### Authentication

- Passwords must be hashed.
- Never store plain text password.
- Login errors should be generic.
- Session/JWT must include user id and role.
- Frontend route guards are not enough; every backend route must check role.

### Role Permissions

Admin:

- Manage users.
- Manage vendors.
- View all procurement records.
- View analytics.

Procurement Officer:

- Create RFQs.
- Assign vendors.
- Compare quotations.
- Initiate approvals.
- Generate POs and invoices after approval.

Vendor:

- View assigned RFQs only.
- Submit and revise own quotations before deadline.
- View own POs and invoice/payment status.

Manager/Approver:

- View assigned approval requests.
- Approve/reject with remarks.
- View budget impact and quotation summary.
- Monitor workflows.

### Input Validation

Validate on both frontend and backend:

- Email format.
- Phone format.
- Password length and confirmation.
- GSTIN format.
- PAN format.
- HSN/SAC format.
- Required vendor fields.
- RFQ deadline must be future.
- Quantities must be positive.
- Prices must be non-negative.
- Quotation cannot be submitted after deadline.
- Reject action requires remarks.
- Vendor cannot access another vendor's RFQ or quotation.
- Status transitions must follow state machine rules.

### API Safety

- Use pagination for list endpoints.
- Use server-side filters, not only frontend filters.
- Use parameterized queries through ORM.
- Restrict attachment extensions and file size.
- Add CORS configuration.
- Add rate limit for login if time permits.
- Log security-relevant events into activity ledger.

## 10. UI/UX Direction

The UI should feel like a quiet operational ERP tool, not a marketing website.

### Layout

- Persistent left sidebar with:
  - Dashboard
  - Vendors
  - RFQs
  - Quotations
  - Approvals
  - Purchase Orders
  - Invoices
  - Reports
  - Activity
- Top bar with current role/user and notification bell.
- Main content should be dense but readable.
- Use tables for operational data.
- Use cards only for KPIs, repeated records, and framed widgets.

### Visual Style

- Professional palette: deep navy/charcoal, green success accents, amber warning, red danger, neutral backgrounds.
- INR amounts should be clear.
- Status badges should be consistent:
  - Draft: gray.
  - Sent/Pending: blue/amber.
  - Approved/Paid: green.
  - Rejected/Blocked/Overdue: red.
- Use icons for actions where obvious: add, edit, download, print, mail, filter, search.
- Avoid decorative gradients and landing-page hero sections.

### Screen-specific Expectations

Dashboard:

- KPI cards.
- ERP process map.
- Pending approval mini-list.
- Active RFQs.
- Recent POs and invoices.
- Spending trend chart.

Vendors:

- Search by name, GST number, category.
- Filters for all/active/pending/blocked.
- Status and compliance badges.

RFQ:

- Line item editor with stable rows.
- Vendor multi-select.
- Deadline.
- Draft and send actions.

Quotation:

- Vendor-facing form.
- Totals computed live.
- Save draft and submit.

Comparison:

- Side-by-side table.
- Lowest price highlight.
- Best Value Score.
- Radar chart or fallback score bars.
- Select and approve action.

Approval:

- Approval chain stepper.
- Budget Impact Preview.
- Policy reason badges.
- Approve/reject with remarks.

PO/Invoice:

- Official document layout.
- GST split.
- Download, print, email.
- 3-way match card.

Activity:

- Timeline.
- Immutable ledger proof with previous hash and entry hash.
- No edit/delete actions.

Reports:

- Vendor performance.
- Procurement stats.
- Spending summary.
- Monthly trend.
- Export button.

## 11. Repository Reference Map

These cloned repositories are reference material. Do not edit them for the hackathon product unless explicitly required.

### Odoo Core

Root:

- `clones-odoo/odoo`

Most important paths:

- `addons/purchase/models/purchase_order.py`
  - RFQ/PO state machine.
  - Portal/mail mixins.
  - Confirmation and approval transition.
  - Invoice creation.
- `addons/purchase/controllers/portal.py`
  - Vendor-facing portal routes for RFQs/POs.
- `addons/account/models/account_move.py`
  - Vendor bill/invoice model, totals, payment state.
- `addons/account/wizard/account_move_send_wizard.py`
  - Invoice send/print/download behavior.
- `addons/mail/models/mail_thread.py`
  - Chatter and activity pattern. Useful for timeline inspiration, but not enough for immutable audit.
- `addons/base_vat/models/res_partner.py`
  - VAT/GSTIN validation inspiration.
- `addons/l10n_in/models/res_partner.py`
  - Indian GST treatment and PAN inspiration.
- `addons/l10n_in/models/product_template.py`
  - HSN/SAC field and validation inspiration.
- `addons/l10n_in_purchase/models/purchase_order.py`
  - GST treatment on purchase orders.
- `addons/l10n_in/data/template/account.tax-in.csv`
  - CGST/SGST/IGST tax group examples.
- `addons/auth_signup`
  - Signup/reset inspiration.
- `addons/web`
  - Odoo UI style reference.

Correction:

- Do not assume `addons/approvals` is available in this public community clone. Approval logic should be implemented in our app using OCA tier validation as inspiration.

### OCA Purchase Workflow

Root:

- `clones-odoo/purchase-workflow`

Most important modules:

- `purchase_request`
  - Purchase request states: draft, to_approve, approved, in_progress, done, rejected.
  - Internal request before RFQ/PO.
- `purchase_request_tier_validation`
  - Tier validation on purchase requests.
- `purchase_tier_validation`
  - Tier validation on purchase orders.
- `purchase_order_approval_block`
  - Approval block reasons and chatter messages.
- `purchase_exception`
  - Policy exception checks before allowing purchase flow.
- `purchase_last_price_info`
  - Last purchase price, supplier, date, and currency. Useful for savings and price anchor.
- `purchase_order_product_recommendation`
  - Product recommendation wizard, useful as pattern only.
- `purchase_invoice_plan`
  - Invoice planning inspiration.
- `purchase_reception_status`
  - Receiving status inspiration for 3-way match lite.

### ERPNext

Root:

- `clones-odoo/erpnext`

Most important paths:

- `erpnext/buying/doctype/request_for_quotation`
  - RFQ lifecycle and supplier portal behavior.
- `erpnext/buying/doctype/supplier_quotation`
  - Supplier quotation model and submitted quote flow.
- `erpnext/buying/report/supplier_quotation_comparison`
  - Supplier quotation comparison report with minimum price highlighting and chart data.
- `erpnext/buying/doctype/supplier_scorecard`
  - Supplier scorecard logic.
- `erpnext/buying/doctype/supplier_scorecard_variable`
  - On-time delivery, delayed shipments, accepted/rejected items, RFQ/SQ metrics.

### Other Local Clones

- `clones-odoo/documentation`
  - Use for Odoo terminology and procurement documentation.
- `clones-odoo/tutorials`
  - Use for Odoo module structure concepts if needed.
- `clones-odoo/partner-contact`
  - Vendor/contact modeling inspiration.
- `clones-odoo/account-invoicing`
  - Invoice warning/payment behavior inspiration if time permits.
- `clones-odoo/reporting-engine`
  - Report/PDF inspiration if time permits.
- `clones-odoo/owl`
  - Only useful if building Odoo-native frontend.
- `clones-odoo/design-themes`
  - Low-priority visual reference.

## 12. Engineering Standards

### Code Organization

Recommended structure:

```text
vendorbridge/
  apps/
    api/
      app/
        auth/
        users/
        vendors/
        rfqs/
        quotations/
        approvals/
        purchase_orders/
        invoices/
        budgets/
        activity_logs/
        reports/
        common/
      migrations/
      tests/
    web/
      src/
        app/
        components/
        features/
        hooks/
        lib/
        routes/
        styles/
  docs/
  docker-compose.yml
  README.md
```

If using a simpler structure, keep the same module separation.

### Service Pattern

Each backend module should have:

- Models/entities.
- Schemas/DTOs.
- Routes/controllers.
- Service/business logic.
- Repository/database access if the framework supports it.
- Tests for complex business rules.

### Logging Rule

Every state transition must call the activity ledger service.

Examples:

- RFQ created.
- RFQ sent.
- Vendor invited.
- Quote draft saved.
- Quote submitted.
- Quote selected.
- Approval requested.
- Approval approved/rejected.
- PO generated.
- Invoice generated.
- Invoice downloaded.
- Invoice printed.
- Invoice emailed.
- Payment status changed.

### Testing Priorities

At minimum, write tests for:

- GSTIN validation.
- HSN/SAC validation.
- Best Value Score calculation.
- Approval threshold routing.
- Budget Impact Preview calculation.
- Immutable hash chain generation.
- State transition guards.
- Vendor access control for RFQs/quotations.

## 13. Demo Data

Use realistic Indian procurement seed data.

Users:

- Admin: `admin@vendorbridge.test`
- Procurement Officer: `officer@vendorbridge.test`
- Manager L1: `rahul.mehta@vendorbridge.test`
- Finance Manager L2: `priya.shah@vendorbridge.test`
- Vendor user: `vendor@infrasupplies.test`

Vendors:

- Infra Supplies Pvt Ltd, Construction/Furniture, Surat, active, rating 4.5.
- TechCore Ltd, IT/Furniture, Ahmedabad, active, rating 3.8.
- OfficeNeed Co, Office Supplies/Furniture, Vadodara, active, rating 4.2.
- FastLog Transport, Logistics, pending or blocked.

RFQ:

- Title: Office Furniture Procurement Q2.
- Category: Furniture.
- Deadline: use a future date during the hackathon.
- Items:
  - Ergonomic chair, quantity 25, unit NOS.
  - Standing desk, quantity 10, unit NOS.

Quotes:

- Infra Supplies: INR 1,85,400, delivery 10 days, payment terms 30 days, rating 4.5.
- TechCore: INR 2,14,800, delivery 7 days, payment terms 15 days, rating 3.8.
- OfficeNeed: INR 2,00,010, delivery 14 days, payment terms 30 days, rating 4.2.

Approval:

- L1: Rahul Mehta, Procurement Head.
- L2: Priya Shah, Finance Manager.

PO/Invoice:

- PO format: `PO-2026-0001`.
- Invoice format: `INV-2026-0001`.
- Company state: Gujarat.
- Vendor state: Gujarat for CGST+SGST demo; add one out-of-state vendor for IGST demo if time permits.

## 14. Presentation Strategy

### Narrative

Do not present this as a CRUD app. Present it as a procurement control system.

Message:

- The problem is not only creating RFQs.
- The real business pain is traceability, decision quality, approval delay, vendor communication, and financial control.
- VendorBridge solves this with structured workflows, relational data design, explainable scoring, budget-aware approvals, GST-aware invoices, and immutable logs.

### Demo Ending

End with the Activity screen.

Show:

- Every event generated during the live demo.
- No edit/delete controls.
- `previous_hash` and `entry_hash`.
- Explain that the database schema intentionally has no soft delete on audit logs.

This directly matches the hidden Excalidraw instruction and the video's database-design emphasis.

## 15. Resolved Questions

All previously-open questions are now decided (see also §0):

- Odoo-native module vs custom app: **Custom app.** The criteria say build from scratch; nothing requires an Odoo module; clones are reference only.
- Backend framework: **FastAPI** (with SQLAlchemy + Alembic).
- Team: **4 members**; ownership in `TASK.md`.
- Deployment: **Local is acceptable and preferred** (criteria favor offline/local). Deploy only if the golden path is done early.
- Email: **`email_outbox` table** is the committed approach; real SMTP only if trivially reliable.
- PDF: **Print-friendly HTML first**, real PDF second.
- Primary database: **PostgreSQL**; SpacetimeDB, DuckDB, and Convex evaluated and rejected (see §4).
- Redis: **Yes**, scoped to analytics caching + rate limiting (see §4/§8).
- Blockchain for logs: **Yes**, as a local blockchain-style ledger; no external/distributed chain (see §8).
- IQ Overview scope: **Adopted** as expanded scope; baseline screens P0, IQ intelligence features P1 (see §3).

## 16. Decision Record

- Use local PostgreSQL as the source of truth.
- Build from scratch, not with Firebase/Supabase/BaaS.
- Use cloned repos for inspiration, not direct modification.
- Keep weighted scoring explainable; do not overclaim AI.
- Prioritize immutable audit logs because the Excalidraw explicitly calls them out.
- Prioritize database schema, validation, and modular backend because the Odoo video says these are heavily evaluated.
- Start implementation after this planning pass. More broad internet research is not required unless rules or competitor claims need pitch citations.
- Stack frozen: FastAPI + SQLAlchemy + Alembic + PostgreSQL + React + TypeScript + Vite + Tailwind + Redis.
- PostgreSQL is the sole system-of-record; experimental databases (SpacetimeDB, DuckDB) and BaaS (Convex) were evaluated and rejected for risk and criteria misfit.
- Redis is used deliberately for caching and rate limiting, not decoration.
- The immutable ledger is blockchain-style (hash chain + Merkle blocks + integrity verification), implemented locally; no external blockchain.
- The VendorBridge IQ intelligence layer (lifecycle, discovery, risk engine, multi-criteria ratings, PO acceptance, delivery tracking; partial fulfillment and split procurement as P1-stretch) is adopted as the differentiator, behind the golden path.
- Treat the must-have hygiene items (clean responsive UI, robust validation, intuitive navigation, dynamic data, team Git) as non-negotiable; database design and the IQ layer are the differentiators.
