import type {
  ActivityLog,
  Approval,
  ApprovalListItem,
  ComparisonResponse,
  DashboardStats,
  Invoice,
  InvoiceListItem,
  LedgerVerification,
  PurchaseOrder,
  PurchaseOrderListItem,
  Quotation,
  QuotationListItem,
  ReportsSummary,
  RFQ,
  RFQListItem,
  TokenResponse,
  UserRole,
  Vendor,
  VendorCategory,
  VendorListResponse,
  VendorStatus,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Request failed";
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export type RegisterPayload = {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  role: UserRole;
  password: string;
};

export type VendorRegistrationFields = {
  company_name: string;
  gstin: string;
  pan?: string;
  state: string;
  city: string;
  category_name: string;
  bank_details?: string;
};

export type VendorPayload = {
  name: string;
  legal_name?: string;
  category_id: number;
  gstin: string;
  pan?: string;
  state: string;
  city: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  status: VendorStatus;
  completed_orders_count: number;
  rating: string;
  reliability_score: string;
  delivery_score: string;
  completion_rate: string;
  satisfaction_score: string;
  compliance_notes?: string;
};

export type RFQPayload = {
  title: string;
  category_id: number;
  description?: string;
  deadline: string;
  vendor_ids: number[];
  items: Array<{
    item_name: string;
    hsn_sac: string;
    quantity: string;
    unit: string;
    target_price?: string;
  }>;
};

export type QuotationPayload = {
  rfq_id: number;
  vendor_id: number;
  delivery_days: number;
  payment_terms_days: number;
  notes?: string;
  items: Array<{
    rfq_item_id: number;
    quantity: string;
    unit_price: string;
    gst_percent: string;
    available_quantity: string;
    additional_quantity: string;
    additional_available_days?: number | null;
  }>;
};

export const api = {
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (payload: RegisterPayload) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  forgotPassword: (email: string) =>
    request<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  me: (token: string) => request<TokenResponse["user"]>("/auth/me", {}, token),
  dashboardStats: (token: string) => request<DashboardStats>("/dashboard/stats", {}, token),
  categories: (token: string) => request<VendorCategory[]>("/vendor-categories", {}, token),
  vendors: (token: string, params: URLSearchParams) =>
    request<VendorListResponse>(`/vendors?${params.toString()}`, {}, token),
  createVendor: (token: string, payload: VendorPayload) =>
    request<Vendor>("/vendors", { method: "POST", body: JSON.stringify(payload) }, token),
  updateVendor: (token: string, id: number, payload: Partial<VendorPayload>) =>
    request<Vendor>(`/vendors/${id}`, { method: "PATCH", body: JSON.stringify(payload) }, token),
  blockVendor: (token: string, id: number) =>
    request<Vendor>(`/vendors/${id}/block`, { method: "POST" }, token),
  unblockVendor: (token: string, id: number) =>
    request<Vendor>(`/vendors/${id}/unblock`, { method: "POST" }, token),
  rfqs: (token: string) => request<RFQListItem[]>("/rfqs", {}, token),
  rfq: (token: string, id: number) => request<RFQ>(`/rfqs/${id}`, {}, token),
  vendorRfqs: (token: string) => request<RFQ[]>("/rfqs/vendor", {}, token),
  createRfq: (token: string, payload: RFQPayload) =>
    request<RFQ>("/rfqs", { method: "POST", body: JSON.stringify(payload) }, token),
  sendRfq: (token: string, id: number) =>
    request<RFQ>(`/rfqs/${id}/send`, { method: "POST" }, token),
  quotations: (token: string) => request<QuotationListItem[]>("/quotations", {}, token),
  saveQuotation: (token: string, payload: QuotationPayload) =>
    request<Quotation>("/quotations/drafts", { method: "POST", body: JSON.stringify(payload) }, token),
  submitQuotation: (token: string, id: number) =>
    request<Quotation>(`/quotations/${id}/submit`, { method: "POST" }, token),
  comparison: (token: string, rfqId: number) =>
    request<ComparisonResponse>(`/rfqs/${rfqId}/comparison`, {}, token),
  selectQuotation: (token: string, rfqId: number, quotationId: number) =>
    request<{ approval_request_id: number }>(
      `/rfqs/${rfqId}/select-quotation`,
      { method: "POST", body: JSON.stringify({ quotation_id: quotationId }) },
      token,
    ),
  approvals: (token: string) => request<ApprovalListItem[]>("/approvals", {}, token),
  approval: (token: string, id: number) => request<Approval>(`/approvals/${id}`, {}, token),
  approve: (token: string, id: number, remarks: string) =>
    request<Approval>(`/approvals/${id}/approve`, { method: "POST", body: JSON.stringify({ remarks }) }, token),
  reject: (token: string, id: number, remarks: string) =>
    request<Approval>(`/approvals/${id}/reject`, { method: "POST", body: JSON.stringify({ remarks }) }, token),
  generatePo: (token: string, approvalId: number) =>
    request<PurchaseOrder>(`/approvals/${approvalId}/purchase-order`, { method: "POST" }, token),
  purchaseOrders: (token: string) => request<PurchaseOrderListItem[]>("/purchase-orders", {}, token),
  purchaseOrder: (token: string, id: number) => request<PurchaseOrder>(`/purchase-orders/${id}`, {}, token),
  acceptPo: (token: string, id: number) =>
    request<PurchaseOrder>(`/purchase-orders/${id}/accept`, { method: "POST", body: JSON.stringify({}) }, token),
  rejectPo: (token: string, id: number) =>
    request<PurchaseOrder>(
      `/purchase-orders/${id}/reject`,
      { method: "POST", body: JSON.stringify({ remarks: "Vendor rejected PO terms." }) },
      token,
    ),
  requestPoModification: (token: string, id: number) =>
    request<PurchaseOrder>(
      `/purchase-orders/${id}/request-modification`,
      { method: "POST", body: JSON.stringify({ remarks: "Vendor requested PO modification." }) },
      token,
    ),
  updateDelivery: (token: string, id: number, statusValue: string) =>
    request<PurchaseOrder>(
      `/purchase-orders/${id}/delivery`,
      { method: "POST", body: JSON.stringify({ status: statusValue }) },
      token,
    ),
  receivePo: (token: string, id: number) =>
    request<PurchaseOrder>(`/purchase-orders/${id}/receive`, { method: "POST" }, token),
  generateInvoice: (token: string, poId: number) =>
    request<Invoice>(`/purchase-orders/${poId}/invoice`, { method: "POST" }, token),
  invoices: (token: string) => request<InvoiceListItem[]>("/invoices", {}, token),
  invoice: (token: string, id: number) => request<Invoice>(`/invoices/${id}`, {}, token),
  markPayable: (token: string, id: number) =>
    request<Invoice>(`/invoices/${id}/payable`, { method: "POST" }, token),
  printInvoice: (token: string, id: number) =>
    request<{ ok: boolean }>(`/invoices/${id}/print`, { method: "POST" }, token),
  emailInvoice: (token: string, id: number, to_email: string) =>
    request<{ id: number }>(
      `/invoices/${id}/email`,
      { method: "POST", body: JSON.stringify({ to_email }) },
      token,
    ),
  reports: (token: string) => request<ReportsSummary>("/reports/summary", {}, token),
  activityLogs: (token: string) => request<ActivityLog[]>("/activity/logs?limit=20", {}, token),
  verifyLedger: (token: string) => request<LedgerVerification>("/activity/verify", {}, token),
};
