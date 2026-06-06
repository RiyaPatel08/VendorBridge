# VendorBridge Proposal: BuzzBeatStrong

Date: 2026-06-06

## One-line Product Positioning

BuzzBeatStrong is a procurement command center for VendorBridge: a role-based source-to-pay ERP that helps teams create RFQs, collect vendor bids, compare best-value offers, run approvals, generate POs and invoices, and preserve every procurement decision in an immutable audit trail.

No proposal can honestly guarantee a hackathon win, but this direction is built to score strongly against the provided problem statement, the Excalidraw screens, Odoo hackathon judging signals, and competitor gaps.

## Ground Truth From The Provided Files

Sources:
- `C:\Users\DELL\Downloads\Vendorbridge Hackathon Problem Statement.pdf`
- `C:\Users\DELL\Documents\VendorBridge - 8 hours.excalidraw`
- Workspace copies: `C:\Users\DELL\Desktop\hckton\odooxksv\Vendorbridge Hackathon Problem Statement.pdf` and `C:\Users\DELL\Desktop\hckton\odooxksv\VendorBridge - 8 hours.excalidraw`

Required core:
- Auth with login, signup, forgot password, session handling, validation, and role-based access.
- Dashboard with pending approvals, active RFQs, recent POs, recent invoices, analytics cards, and quick actions.
- Vendor management with registration, status, category, GST details, contacts, search, and filters.
- RFQ creation with title, item lines, quantities, attachments, deadline, and vendor assignment.
- Vendor quotation submission with pricing, delivery timeline, notes, editable drafts, and final submit.
- Quotation comparison with side-by-side comparison, lowest price highlighting, delivery comparison, vendor rating, sort, and filter.
- Approval workflow with approve/reject, remarks, timeline, state transitions, and tracking.
- PO and invoice generation with auto PO number, tax and total calculations, PDF download, print, email, and status updates.
- Activity logs and notifications for RFQs, approvals, invoices, and audit trail.
- Reports and analytics with vendor performance, procurement statistics, spending summaries, trends, and export.

Important Excalidraw-specific detail:
- The audit logs screen explicitly says logs must be immutable, write-once, and must not support edit/delete or soft-delete. This should be treated as a must-have differentiator, not a hidden technical detail.

## High-value Repositories To Clone

### Clone First

1. https://github.com/odoo/odoo
   - Main Odoo source.
   - Study these addons first:
     - `addons/purchase` for RFQ and PO structure.
     - `addons/purchase_requisition` for purchase agreements/call-for-tenders style flows.
     - `addons/purchase_stock` for receiving and inventory handoff ideas.
     - `addons/account` and `addons/account_payment` for invoice, tax, bill, and payment patterns.
     - `addons/mail` and `addons/bus` for chatter, notifications, and activity style.
     - `addons/portal` for vendor-facing portal ideas.
     - `addons/contacts`, `addons/product`, `addons/base_vat`, `addons/l10n_in_purchase_stock` for vendor/product/GST direction.
     - `addons/auth_signup`, `addons/auth_password_policy`, `addons/auth_timeout`, `addons/auth_totp` for auth inspiration.
     - `addons/board`, `addons/spreadsheet_dashboard`, `addons/spreadsheet_dashboard_account`, `addons/spreadsheet_dashboard_stock_account` for dashboard/reporting ideas.
     - `addons/web` for Odoo-style UI patterns.

2. https://github.com/odoo/documentation
   - Use it to understand Odoo's terminology and expected ERP flow.
   - Especially RFQs, purchase agreements, vendor bills, purchase reports, activities, and reporting essentials.

3. https://github.com/odoo/tutorials
   - Best for quickly understanding how Odoo modules are structured.

4. https://github.com/OCA/purchase-workflow
   - Not official Odoo SA, but extremely relevant Odoo ecosystem code.
   - Study:
     - `purchase_request`
     - `purchase_request_tier_validation`
     - `purchase_request_to_requisition`
     - `purchase_tier_validation`
     - `purchase_order_approval_block`
     - `purchase_exception`
     - `purchase_last_price_info`
     - `purchase_order_product_recommendation`
     - `purchase_order_type_dashboard`
     - `purchase_invoice_plan`
     - `purchase_reception_status`

5. https://github.com/OCA/partner-contact
   - Vendor profile, contacts, addresses, and partner data structure ideas.

### Clone If Time Allows

- https://github.com/OCA/account-invoicing
- https://github.com/OCA/account-invoice-reporting
- https://github.com/OCA/reporting-engine
- https://github.com/OCA/report-print-send
- https://github.com/OCA/queue
- https://github.com/OCA/web
- https://github.com/odoo/owl
- https://github.com/odoo/o-spreadsheet
- https://github.com/odoo/paper-muncher

## What The Market Teaches

Competitor patterns worth borrowing:

- Zoho Procurement focuses on source-to-pay coverage: purchase requests, RFQs, vendor management, approvals, POs, receiving, invoices, payments, analytics, audit trails, supplier portal, AI extraction, and PO/GRN/invoice matching.
- SAP Ariba emphasizes AI-assisted sourcing, supplier recommendations, smart scoring, bid comparisons, historical data, reminders, approvals, supplier discovery, and certifications.
- Microsoft Dynamics 365 has strong vendor collaboration: vendors can work with POs, invoices, RFQs, consignment data, and vendor master data; it also supports alternates, attachments, comments, PO external review, and versioning.
- Oracle Procurement highlights supplier self-service, onboarding, supplier data, certifications, financial metrics, scorecards, risk attributes, guided journeys, and AI negotiation assistance.
- ERPNext proves that an open-source ERP can expose RFQs through a supplier portal and automatically create supplier quotations from vendor-submitted RFQ responses.

Translation for VendorBridge:
- Do not build only CRUD screens.
- Build a full source-to-pay flow with visible state transitions.
- Make vendor collaboration real.
- Make comparison smarter than "lowest price wins".
- Make auditability visible.
- Make reports prove business value.

## BuzzBeatStrong USPs

### 1. Best Value Quote Score

The comparison screen should show:
- Lowest price.
- Delivery days.
- Vendor rating.
- GST/compliance status.
- Past fulfillment score.
- Payment terms.
- Risk flags.
- Final "Best Value Score".

Why it wins: the base statement asks for comparison and rating; this turns that into an explainable procurement decision.

Suggested formula:

```text
score =
  price_score * 0.40 +
  delivery_score * 0.20 +
  vendor_rating * 0.15 +
  compliance_score * 0.15 +
  payment_terms_score * 0.10
```

### 2. Immutable Procurement Ledger

Every important event is appended to `activity_logs`:
- RFQ created.
- Vendor invited.
- Quote submitted/edited.
- Quote selected.
- Approval requested.
- Approval accepted/rejected.
- PO generated.
- Invoice generated/downloaded/printed/emailed.
- Payment status changed.

Add a `previous_hash` and `entry_hash` field to make the trail tamper-evident in the demo.

Critical rule:
- No update endpoint.
- No delete endpoint.
- No soft-delete field.
- Database trigger or ORM guard rejects update/delete.

### 3. Vendor Portal That Feels Real

Vendor users should see:
- Assigned RFQs.
- Deadline and status.
- Item table.
- Attachment download.
- Quote draft.
- Submit/revise quotation.
- PO status after selection.
- Invoice/payment status if applicable.

Hackathon-friendly enhancement:
- Use secure invite tokens or magic links for RFQ access.

### 4. 3-Way Match Lite

Before marking an invoice as payable/paid, show:
- PO amount.
- Received/accepted quantity.
- Invoice amount.
- Difference flag.

Even a simplified "received/accepted" checkbox per PO line makes the invoice screen feel ERP-grade.

### 5. Policy-Aware Approval Engine

Approval rules:
- Amount threshold.
- Category.
- Unverified vendor.
- Missing GST details.
- Best-value score below threshold.
- Single quote received.

Approver screen should show why approval was required, not just approve/reject buttons.

### 6. Savings And Risk Analytics

Reports should show:
- Total spend.
- Active vendors.
- PO fulfillment percentage.
- Overdue invoices.
- Savings captured: average quote or next-best quote minus selected quote.
- Vendor win rate.
- Average delivery time.
- Category-wise spend.
- Export CSV/PDF.

This makes the product's business value obvious during judging.

## MVP Scope For An 8-hour Build

### P0: Must Finish

- Auth and roles: Admin, Procurement Officer, Vendor, Manager.
- Dashboard with seeded live database counts.
- Vendor CRUD with GST/status/category/search/filter.
- RFQ creation with line items, vendors, deadline, attachment placeholder.
- Vendor quotation submission.
- Quote comparison table with lowest-price highlight.
- Select quote and start approval.
- Approval approve/reject with remarks.
- Generate PO and invoice from approved quote.
- PDF/download/print/email buttons, even if email is logged rather than truly sent.
- Activity timeline and append-only audit log.
- Reports page with at least 4 KPIs and export.

### P1: Winning Layer

- Best Value Score and explainable score breakdown.
- Immutable log hash chain.
- Approval policy reason badges.
- 3-way match lite.
- Vendor compliance badge.
- Demo email outbox/log for sent invoices/RFQs.
- "ERP process map" on dashboard showing RFQ -> Quotes -> Approval -> PO -> Invoice -> Paid.

### P2: Stretch Only If P0/P1 Are Stable

- AI-generated quote comparison summary.
- OCR/PDF quote extraction.
- WhatsApp/email reminders.
- Vendor magic-link RFQ access.
- Offline draft caching.
- Supplier risk or ESG fields.

## Recommended Demo Story

1. Admin logs in and shows role-based dashboard.
2. Procurement Officer creates "Office Furniture Q2" RFQ with two line items and assigns three vendors.
3. Vendor logs in, sees assigned RFQ, submits quote with price, delivery date, GST, payment terms, and notes.
4. Procurement Officer opens comparison screen. Lowest price is highlighted, but Best Value Score recommends the most reliable vendor.
5. Officer selects the vendor. The app automatically starts approval and logs the event.
6. Manager opens approval page, sees policy reason and quote summary, approves with remarks.
7. App generates PO number and invoice with GST totals.
8. User downloads PDF, prints, and sends invoice by email; each action appears in the immutable timeline.
9. Reports page shows spend, savings captured, active vendors, overdue invoices, PO fulfillment, and export.
10. Final punch: open activity logs and show the hash-linked write-once audit ledger.

## Suggested Data Model

Core tables:
- `users`
- `roles`
- `vendors`
- `vendor_categories`
- `vendor_documents`
- `rfqs`
- `rfq_items`
- `rfq_vendor_invites`
- `quotations`
- `quotation_items`
- `approval_requests`
- `approval_steps`
- `purchase_orders`
- `purchase_order_items`
- `invoices`
- `invoice_items`
- `attachments`
- `notifications`
- `activity_logs`
- `vendor_score_snapshots`

Important states:
- RFQ: `draft`, `published`, `quotes_received`, `comparison`, `approval_pending`, `approved`, `po_generated`, `closed`, `cancelled`.
- Quotation: `draft`, `submitted`, `revised`, `selected`, `rejected`.
- Approval: `pending`, `approved`, `rejected`, `needs_revision`.
- PO: `draft`, `sent`, `vendor_accepted`, `received`, `invoiced`, `closed`.
- Invoice: `draft`, `generated`, `sent`, `paid`, `overdue`, `cancelled`.

## Pitch Script

"VendorBridge solves procurement from RFQ to invoice, but BuzzBeatStrong adds the layer procurement teams actually need under pressure: explainable vendor selection and audit-safe approvals. A buyer can publish an RFQ, vendors submit quotations from their portal, the system ranks offers by best value instead of only lowest price, managers approve with policy reasons, and the approved quote becomes a PO and invoice. Every event is stored in a write-once ledger, so the organization can defend every procurement decision later. This is not just a form app; it is a source-to-pay ERP workflow with compliance, collaboration, and measurable savings."

## Source Links Consulted

- Odoo GitHub: https://github.com/odoo
- Odoo main repo: https://github.com/odoo/odoo
- Odoo documentation: https://github.com/odoo/documentation
- Odoo tutorials: https://github.com/odoo/tutorials
- OCA purchase workflow: https://github.com/OCA/purchase-workflow
- OCA partner contact: https://github.com/OCA/partner-contact
- OCA account invoicing: https://github.com/OCA/account-invoicing
- OCA reporting engine: https://github.com/OCA/reporting-engine
- OCA report print/send: https://github.com/OCA/report-print-send
- Odoo RFQ documentation: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html
- Odoo vendor bills / 3-way matching: https://www.odoo.com/documentation/master/applications/inventory_and_mrp/purchase/manage_deals/manage.html
- Odoo purchase analysis: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/advanced/analyze.html
- Odoo vendor costs report: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/advanced/vendor_costs_report.html
- Odoo x SPIT Hackathon 2025: https://www.odoo.com/event/odoo-x-spit-hackathon-2025-8711
- Odoo Hackathon 2026 listing: https://internshala.com/competitions/odoo-hackathon-2026/
- Zoho Procurement: https://www.zoho.com/procurement/
- Zoho Spend Procurement: https://www.zoho.com/spend/procurement/
- SAP Ariba Sourcing: https://www.sap.com/products/spend-management/ariba-sourcing.html
- Microsoft Dynamics procurement overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-sourcing-overview
- Microsoft Dynamics vendor collaboration: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/vendor-collaboration-work-external-vendors
- Oracle Procurement: https://www.oracle.com/erp/procurement/
- ERPNext supplier quotation portal: https://docs.frappe.io/erpnext/user/manual/en/how-to-create-a-supplier-quotation-through-the-supplier-portal
