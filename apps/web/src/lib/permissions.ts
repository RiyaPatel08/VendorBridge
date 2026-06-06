import type { UserRole } from "./types";

export type ViewKey =
  | "dashboard"
  | "vendors"
  | "rfqs"
  | "quotations"
  | "approvals"
  | "purchaseOrders"
  | "invoices"
  | "reports"
  | "activity";

export type Permission =
  | "viewVendors"
  | "verifyVendors"
  | "manageVendorStatus"
  | "createRfq"
  | "sendRfq"
  | "submitQuotation"
  | "compareQuotations"
  | "selectQuotation"
  | "viewApprovals"
  | "approvePurchases"
  | "generatePurchaseOrder"
  | "acceptPurchaseOrder"
  | "updateDelivery"
  | "receivePurchaseOrder"
  | "generateInvoice"
  | "markInvoicePayable"
  | "viewReports"
  | "viewLedger"
  | "verifyLedger";

export const ROLE_VIEWS: Record<UserRole, ViewKey[]> = {
  admin: ["dashboard", "vendors", "rfqs", "reports", "activity"],
  procurement_officer: [
    "dashboard",
    "vendors",
    "rfqs",
    "quotations",
    "purchaseOrders",
    "invoices",
    "reports",
  ],
  manager: [
    "dashboard",
    "rfqs",
    "quotations",
    "approvals",
    "purchaseOrders",
    "invoices",
    "reports",
  ],
  finance_manager: [
    "dashboard",
    "rfqs",
    "quotations",
    "approvals",
    "purchaseOrders",
    "invoices",
    "reports",
  ],
  vendor: ["dashboard", "rfqs", "quotations", "purchaseOrders", "invoices"],
};

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: [
    "viewVendors",
    "verifyVendors",
    "manageVendorStatus",
    "viewReports",
    "viewLedger",
    "verifyLedger",
  ],
  procurement_officer: [
    "viewVendors",
    "createRfq",
    "sendRfq",
    "compareQuotations",
    "selectQuotation",
    "generatePurchaseOrder",
    "receivePurchaseOrder",
    "generateInvoice",
    "viewReports",
  ],
  manager: [
    "compareQuotations",
    "viewApprovals",
    "approvePurchases",
    "generatePurchaseOrder",
    "receivePurchaseOrder",
    "generateInvoice",
    "markInvoicePayable",
    "viewReports",
  ],
  finance_manager: [
    "compareQuotations",
    "viewApprovals",
    "approvePurchases",
    "generatePurchaseOrder",
    "receivePurchaseOrder",
    "generateInvoice",
    "markInvoicePayable",
    "viewReports",
  ],
  vendor: ["submitQuotation", "acceptPurchaseOrder", "updateDelivery"],
};

export function defaultViewForRole(role: UserRole): ViewKey {
  return ROLE_VIEWS[role]?.[0] ?? "dashboard";
}

export function canAccessView(role: UserRole, view: ViewKey): boolean {
  return (ROLE_VIEWS[role] ?? []).includes(view);
}

export function can(role: UserRole | undefined, permission: Permission): boolean {
  if (!role) return false;
  return (ROLE_PERMISSIONS[role] ?? []).includes(permission);
}

export function roleLabel(role: UserRole): string {
  const map: Record<UserRole, string> = {
    admin: "Admin",
    procurement_officer: "Procurement Officer",
    manager: "Manager / Approver",
    finance_manager: "Manager / Approver",
    vendor: "Vendor",
  };
  return map[role] ?? role;
}

export function roleBadgeColor(role: UserRole): string {
  const map: Record<UserRole, string> = {
    admin: "bg-primary/10 text-primary border-primary/20",
    procurement_officer: "bg-secondary/10 text-secondary border-secondary/20",
    manager: "bg-tertiary/10 text-tertiary border-tertiary/20",
    finance_manager: "bg-tertiary/10 text-tertiary border-tertiary/20",
    vendor: "bg-primary-container/40 text-on-primary-container border-primary-container",
  };
  return map[role] ?? "bg-surface-container text-on-surface-variant border-outline-variant";
}
