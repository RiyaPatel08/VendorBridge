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
  purchase_orders: number;
  invoices: number;
  ledger_entries: number;
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

