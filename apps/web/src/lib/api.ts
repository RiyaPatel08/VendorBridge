import type {
  ActivityLog,
  DashboardStats,
  LedgerVerification,
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
  activityLogs: (token: string) => request<ActivityLog[]>("/activity/logs?limit=20", {}, token),
  verifyLedger: (token: string) => request<LedgerVerification>("/activity/verify", {}, token),
};

