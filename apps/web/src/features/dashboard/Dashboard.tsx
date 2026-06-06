import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";
import type { DashboardStats } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

const initialStats: DashboardStats = {
  vendors: 0,
  active_vendors: 0,
  rfqs: 0,
  active_rfqs: 0,
  pending_approvals: 0,
  purchase_orders: 0,
  invoices: 0,
  ledger_entries: 0,
  recent_purchase_orders: [],
  recent_invoices: [],
};

const STATUS_PILL: Record<string, string> = {
  active: "bg-secondary/10 text-secondary border border-secondary/20",
  pending: "bg-primary-container/30 text-primary border border-primary/20",
  blocked: "bg-error-container text-on-error-container border border-error/20",
  accepted: "bg-secondary/10 text-secondary border border-secondary/20",
  rejected: "bg-error-container text-on-error-container border border-error/20",
  draft: "bg-surface-container text-on-surface-variant border border-outline-variant",
  sent: "bg-primary/10 text-primary border border-primary/20",
  closed: "bg-surface-container-high text-on-surface-variant border border-outline-variant",
  payable: "bg-secondary/10 text-secondary border border-secondary/20",
  paid: "bg-tertiary/10 text-tertiary border border-tertiary/20",
};

function StatusPill({ value }: { value: string }) {
  const cls = STATUS_PILL[value?.toLowerCase()] ?? STATUS_PILL.draft;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${cls}`}>
      {value?.replace(/_/g, " ")}
    </span>
  );
}

export function Dashboard({ token }: { token: string }) {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>(initialStats);
  const [error, setError] = useState<string | null>(null);

  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
  const role = user?.role;
  const isApprover = role === "manager" || role === "finance_manager";

  useEffect(() => {
    api
      .dashboardStats(token)
      .then(setStats)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load dashboard"));
  }, [token]);

  const statCards = [
    {
      label: role === "vendor" ? "RFQs Received" : "Active RFQs",
      value: role === "vendor" ? stats.rfqs : stats.active_rfqs,
      accent: "border-l-primary",
      iconBg: "bg-primary/10 text-primary",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
        </svg>
      ),
    },
    {
      label: "Pending Approvals",
      value: stats.pending_approvals,
      accent: "border-l-error",
      iconBg: "bg-error-container text-on-error-container",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3z"/>
        </svg>
      ),
    },
    {
      label: "Purchase Orders",
      value: stats.purchase_orders,
      accent: "border-l-secondary",
      iconBg: "bg-secondary/10 text-secondary",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/>
        </svg>
      ),
    },
    {
      label: "Invoices",
      value: stats.invoices,
      accent: "border-l-tertiary",
      iconBg: "bg-tertiary/10 text-tertiary",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/>
        </svg>
      ),
    },
  ].filter((card) => isApprover || card.label !== "Pending Approvals");

  const summaryCards =
    role === "vendor"
      ? [
          { label: "My RFQs", value: stats.rfqs },
          { label: "My Purchase Orders", value: stats.purchase_orders },
          { label: "My Invoices", value: stats.invoices },
          { label: "Active Profile", value: stats.active_vendors ? "Yes" : "No" },
        ]
      : role === "admin"
        ? [
            { label: "Total Vendors", value: stats.vendors },
            { label: "Active Vendors", value: stats.active_vendors },
            { label: "Total RFQs", value: stats.rfqs },
            { label: "Ledger Entries", value: stats.ledger_entries },
          ]
        : isApprover
          ? [
              { label: "Pending Approvals", value: stats.pending_approvals },
              { label: "Total RFQs", value: stats.rfqs },
              { label: "Purchase Orders", value: stats.purchase_orders },
              { label: "Invoices", value: stats.invoices },
            ]
          : [
              { label: "Active Vendors", value: stats.active_vendors },
              { label: "Total RFQs", value: stats.rfqs },
              { label: "Purchase Orders", value: stats.purchase_orders },
              { label: "Invoices", value: stats.invoices },
            ];

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg bg-error-container border border-error/20 px-4 py-3 text-sm text-on-error-container">
          {error}
        </div>
      )}

      {/* Welcome header */}
      <div>
        <h2 className="font-headline-md text-headline-md text-on-surface">
          Welcome back, {user?.first_name ?? "User"}
        </h2>
        <p className="text-body-base text-on-surface-variant mt-0.5">
          Here is your procurement overview for {today}.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div
            key={card.label}
            className={`bg-surface-container-lowest border-l-4 ${card.accent} border-y border-r border-outline-variant rounded-lg p-5 shadow-card flex flex-col gap-2`}
          >
            <div className="flex justify-between items-start">
              <p className="text-label-bold text-on-surface-variant uppercase tracking-wider">{card.label}</p>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${card.iconBg}`}>
                {card.icon}
              </div>
            </div>
            <p className="font-display-lg text-display-lg text-on-surface mt-1">{card.value}</p>
          </div>
        ))}
      </div>

      {/* Recent tables */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Recent Purchase Orders */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-bright">
            <h3 className="font-title-sm text-title-sm text-on-surface">Recent Purchase Orders</h3>
            <span className="text-label-bold text-label-bold text-on-surface-variant">{stats.purchase_orders} total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-on-surface-variant border-b border-outline-variant">
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide">PO No.</th>
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide">Vendor</th>
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide">Status</th>
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant text-body-dense">
                {stats.recent_purchase_orders.map((po) => (
                  <tr key={po.id} className="hover:bg-surface-container-low transition-colors">
                    <td className="px-4 py-3 font-mono text-primary text-xs">{po.po_number}</td>
                    <td className="px-4 py-3 text-on-surface font-medium">{po.vendor_name}</td>
                    <td className="px-4 py-3">
                      <StatusPill value={po.delivery_status} />
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-on-surface">
                      ₹{po.grand_total.toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
                {!stats.recent_purchase_orders.length && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-on-surface-variant text-sm">
                      No purchase orders yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Invoices */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-bright">
            <h3 className="font-title-sm text-title-sm text-on-surface">Recent Invoices</h3>
            <span className="text-label-bold text-label-bold text-on-surface-variant">{stats.invoices} total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-on-surface-variant border-b border-outline-variant">
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide">Invoice No.</th>
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide">Vendor</th>
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide">Status</th>
                  <th className="px-4 py-2.5 text-label-bold text-label-bold font-semibold uppercase tracking-wide text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant text-body-dense">
                {stats.recent_invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-surface-container-low transition-colors">
                    <td className="px-4 py-3 font-mono text-primary text-xs">{inv.invoice_number}</td>
                    <td className="px-4 py-3 text-on-surface font-medium">{inv.vendor_name}</td>
                    <td className="px-4 py-3">
                      <StatusPill value={inv.status} />
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-on-surface">
                      ₹{inv.grand_total.toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
                {!stats.recent_invoices.length && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-on-surface-variant text-sm">
                      No invoices yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {summaryCards.map((item) => (
          <div key={item.label} className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-card">
            <p className="text-label-sm text-label-sm text-on-surface-variant uppercase tracking-wide">{item.label}</p>
            <p className="font-title-sm text-title-sm text-on-surface mt-2">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
