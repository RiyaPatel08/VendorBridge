export type UserRole =
  | "admin"
  | "procurement_officer"
  | "vendor"
  | "manager"
  | "finance_manager";

export type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type VendorStatus = "pending" | "active" | "blocked";
export type LifecycleStage = "potential" | "emerging" | "verified" | "trusted" | "preferred";

export type VendorCategory = {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
};

export type Vendor = {
  id: number;
  name: string;
  legal_name: string | null;
  category_id: number;
  gstin: string;
  pan: string | null;
  state: string;
  city: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  status: VendorStatus;
  lifecycle_stage: LifecycleStage;
  completed_orders_count: number;
  rating: string;
  reliability_score: string;
  delivery_score: string;
  completion_rate: string;
  satisfaction_score: string;
  is_gstin_verified: boolean;
  is_pan_verified: boolean;
  compliance_notes: string | null;
  compliance_badge: "compliant" | "needs_review" | "blocked";
  created_at: string;
  updated_at: string;
};

export type VendorListResponse = {
  items: Vendor[];
  page: number;
  page_size: number;
  total: number;
};

export type DashboardStats = {
  vendors: number;
  active_vendors: number;
  rfqs: number;
  active_rfqs: number;
  pending_approvals: number;
  purchase_orders: number;
  invoices: number;
  ledger_entries: number;
  recent_purchase_orders: Array<{
    id: number;
    po_number: string;
    vendor_name: string;
    status: string;
    delivery_status: string;
    grand_total: number;
  }>;
  recent_invoices: Array<{
    id: number;
    invoice_number: string;
    vendor_name: string;
    status: string;
    match_status: string;
    grand_total: number;
  }>;
  spending_trend: Array<{ month: string; spend: number }>;
  lifecycle_distribution: Array<{ stage: string; count: number }>;
};

export type ActivityLog = {
  id: number;
  actor_id: number | null;
  event_type: string;
  entity_type: string;
  entity_id: number | null;
  summary: string;
  payload: Record<string, unknown>;
  previous_hash: string;
  entry_hash: string;
  block_id: number | null;
  created_at: string;
};

export type LedgerVerification = {
  ok: boolean;
  checked_entries: number;
  checked_blocks: number;
  message: string;
  first_error_log_id: number | null;
};

export type RFQStatus = "draft" | "sent" | "closed" | "cancelled";
export type QuotationStatus = "draft" | "submitted" | "selected" | "rejected";
export type ApprovalStatus = "pending" | "approved" | "rejected";

export type RFQItem = {
  id: number;
  item_name: string;
  hsn_sac: string;
  quantity: string;
  unit: string;
  target_price: string | null;
};

export type RFQInvite = {
  id: number;
  vendor_id: number;
  vendor_name: string;
  status: string;
  discovery_source: string;
  vendor_lifecycle_stage_at_invite: string;
};

export type RFQ = {
  id: number;
  title: string;
  category_id: number;
  category_name: string | null;
  description: string | null;
  deadline: string;
  status: RFQStatus;
  created_by_id: number;
  items: RFQItem[];
  invites: RFQInvite[];
  created_at: string;
  updated_at: string;
};

export type RFQListItem = {
  id: number;
  title: string;
  category_name: string | null;
  deadline: string;
  status: RFQStatus;
  quote_count: number;
  invite_count: number;
  created_at: string;
};

export type Quotation = {
  id: number;
  rfq_id: number;
  vendor_id: number;
  vendor_name: string | null;
  status: QuotationStatus;
  delivery_days: number;
  payment_terms_days: number;
  notes: string | null;
  subtotal: string;
  gst_total: string;
  grand_total: string;
  best_value_score: string;
  score_breakdown: Record<string, number> | null;
  submitted_at: string | null;
  items: Array<{
    id: number;
    rfq_item_id: number;
    item_name: string | null;
    quantity: string;
    unit_price: string;
    gst_percent: string;
    available_quantity: string;
    additional_quantity: string;
    additional_available_days: number | null;
    line_subtotal: string;
    line_gst: string;
    line_total: string;
  }>;
  created_at: string;
  updated_at: string;
};

export type QuotationListItem = {
  id: number;
  rfq_id: number;
  rfq_title: string;
  vendor_id: number;
  vendor_name: string;
  status: QuotationStatus;
  grand_total: string;
  delivery_days: number;
  best_value_score: string;
  submitted_at: string | null;
};

export type ComparisonRow = {
  quotation_id: number;
  vendor_id: number;
  vendor_name: string;
  vendor_rating: string;
  lifecycle_stage: string;
  status: QuotationStatus;
  subtotal: string;
  gst_total: string;
  grand_total: string;
  delivery_days: number;
  payment_terms_days: number;
  best_value_score: string;
  score_breakdown: Record<string, number>;
  is_lowest_price: boolean;
  coverage_label: string;
};

export type ComparisonResponse = {
  rfq_id: number;
  rfq_title: string;
  rows: ComparisonRow[];
};

export type Approval = {
  id: number;
  rfq_id: number;
  rfq_title: string;
  quotation_id: number;
  vendor_id: number;
  vendor_name: string;
  requested_by_id: number;
  status: ApprovalStatus;
  risk_tier: string | null;
  risk_breakdown: Record<string, number> | null;
  budget_impact: Record<string, number | string> | null;
  policy_reasons: string[] | null;
  remarks: string | null;
  quote_total: string;
  steps: Array<{
    id: number;
    approver_id: number;
    approver_name: string;
    sequence: number;
    status: ApprovalStatus;
    remarks: string | null;
    decided_at: string | null;
  }>;
  created_at: string;
  updated_at: string;
};

export type ApprovalListItem = {
  id: number;
  rfq_title: string;
  vendor_name: string;
  status: ApprovalStatus;
  quote_total: string;
  risk_tier: string | null;
  created_at: string;
};

export type PurchaseOrder = {
  id: number;
  po_number: string;
  approval_request_id: number | null;
  vendor_id: number;
  vendor_name: string;
  status: string;
  acceptance_status: string;
  delivery_status: string;
  subtotal: string;
  gst_total: string;
  grand_total: string;
  items: Array<{
    id: number;
    item_name: string;
    hsn_sac: string;
    quantity: string;
    unit_price: string;
    received_quantity: string;
    accepted_quantity: string;
  }>;
  created_at: string;
  updated_at: string;
};

export type PurchaseOrderListItem = {
  id: number;
  po_number: string;
  vendor_name: string;
  status: string;
  acceptance_status: string;
  delivery_status: string;
  grand_total: string;
  created_at: string;
};

export type Invoice = {
  id: number;
  invoice_number: string;
  purchase_order_id: number;
  po_number: string;
  vendor_id: number;
  vendor_name: string;
  vendor_gstin: string;
  invoice_date: string;
  due_date: string;
  status: string;
  subtotal: string;
  cgst_total: string;
  sgst_total: string;
  igst_total: string;
  grand_total: string;
  match_status: string;
  items: Array<{
    id: number;
    item_name: string;
    hsn_sac: string;
    quantity: string;
    unit_price: string;
    gst_percent: string;
    line_total: string;
  }>;
  created_at: string;
  updated_at: string;
};

export type InvoiceListItem = {
  id: number;
  invoice_number: string;
  po_number: string;
  vendor_name: string;
  status: string;
  match_status: string;
  grand_total: string;
  due_date: string;
};

export type ReportsSummary = {
  kpis: {
    total_spend: number;
    pending_approvals: number;
    rfqs: number;
    quotations: number;
  };
  monthly_spend: Array<{ month: string; spend: number }>;
  categories: Array<{ category: string; vendors: number; spend: number }>;
  vendors: Array<{
    id: number;
    name: string;
    rating: number;
    lifecycle_stage: string;
    reliability_score: number;
    delivery_score: number;
    completed_orders_count: number;
  }>;
};
