import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
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
  spending_trend: [],
  lifecycle_distribution: [],
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
  not_started: "bg-surface-container text-on-surface-variant border border-outline-variant",
  shipped: "bg-primary/10 text-primary border border-primary/20",
  in_transit: "bg-primary-container/30 text-primary border border-primary/20",
  delivered: "bg-secondary/10 text-secondary border border-secondary/20",
  matched: "bg-secondary/10 text-secondary border border-secondary/20",
};

const LIFECYCLE_COLORS: Record<string, string> = {
  potential: "#80747b",
  emerging: "#60d9d5",
  verified: "#6d4262",
  trusted: "#006a68",
  preferred: "#005d1e",
};

const PROCESS_STEPS = [
  { key: "rfq", label: "RFQ", icon: "📋" },
  { key: "quotes", label: "Quotes", icon: "💬" },
  { key: "approval", label: "Approval", icon: "✅" },
  { key: "po", label: "PO", icon: "🛒" },
  { key: "invoice", label: "Invoice", icon: "🧾" },
  { key: "paid", label: "Paid", icon: "💰" },
];

function StatusPill({ value }: { value: string }) {
  const cls = STATUS_PILL[value?.toLowerCase()] ?? STATUS_PILL.draft;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${cls}`}>
      {value?.replace(/_/g, " ")}
    </span>
  );
}

function ProcessMap({ stats }: { stats: DashboardStats }) {
  const stepCounts = [
    stats.active_rfqs,
    stats.rfqs > 0 ? "—" : 0,
    stats.pending_approvals,
    stats.purchase_orders,
    stats.invoices,
    "—",
  ];

  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card p-5">
      <h3 className="font-title-sm text-title-sm text-on-surface mb-4">ERP Procurement Workflow</h3>
      <div className="flex items-center justify-between gap-1 overflow-x-auto">
        {PROCESS_STEPS.map((step, i) => (
          <div key={step.key} className="flex items-center min-w-0">
            <div className="flex flex-col items-center min-w-[70px]">
              <div className="w-11 h-11 rounded-full bg-primary-container flex items-center justify-center text-lg shadow-sm">
                {step.icon}
              </div>
              <p className="mt-1.5 text-xs font-bold text-on-surface">{step.label}</p>
              <p className="text-[11px] text-on-surface-variant font-semibold">{stepCounts[i]}</p>
            </div>
            {i < PROCESS_STEPS.length - 1 && (
              <div className="flex-1 min-w-[20px] mx-1">
                <div className="h-0.5 bg-gradient-to-r from-primary-container to-outline-variant rounded-full" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
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
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
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
          <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
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

      {/* ERP Process Map */}
      <ProcessMap stats={stats} />

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

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-[1.2fr_0.8fr] gap-4">
        {/* Spending Trend Area Chart */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
            <h3 className="font-title-sm text-title-sm text-on-surface">Spending Trend</h3>
            <p className="text-label-sm text-on-surface-variant mt-0.5">Monthly procurement spend from invoices</p>
          </div>
          <div className="p-4 h-64">
            {stats.spending_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.spending_trend}>
                  <defs>
                    <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6d4262" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6d4262" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e1e2e4" />
                  <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#4e444a" }} />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#4e444a" }}
                    tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#fff",
                      border: "1px solid #d2c2ca",
                      borderRadius: "8px",
                      fontSize: "13px",
                    }}
                    formatter={(value: number) => [`₹${value.toLocaleString("en-IN")}`, "Spend"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="spend"
                    stroke="#6d4262"
                    strokeWidth={2.5}
                    fill="url(#spendGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-on-surface-variant text-sm">
                No invoice data yet
              </div>
            )}
          </div>
        </div>

        {/* Vendor Lifecycle Distribution Pie Chart */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
            <h3 className="font-title-sm text-title-sm text-on-surface">Vendor Ecosystem</h3>
            <p className="text-label-sm text-on-surface-variant mt-0.5">Distribution by lifecycle stage</p>
          </div>
          <div className="p-4 h-64">
            {stats.lifecycle_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.lifecycle_distribution}
                    dataKey="count"
                    nameKey="stage"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    strokeWidth={2}
                    stroke="#fff"
                  >
                    {stats.lifecycle_distribution.map((entry) => (
                      <Cell
                        key={entry.stage}
                        fill={LIFECYCLE_COLORS[entry.stage] ?? "#80747b"}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "#fff",
                      border: "1px solid #d2c2ca",
                      borderRadius: "8px",
                      fontSize: "13px",
                    }}
                    formatter={(value: number, name: string) => [value, name.charAt(0).toUpperCase() + name.slice(1)]}
                  />
                  <Legend
                    verticalAlign="bottom"
                    formatter={(value: string) => (
                      <span className="text-xs font-semibold text-on-surface-variant capitalize">{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-on-surface-variant text-sm">
                No vendor data yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent tables */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Recent Purchase Orders */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-bright">
            <h3 className="font-title-sm text-title-sm text-on-surface">Recent Purchase Orders</h3>
            <span className="text-label-bold text-on-surface-variant">{stats.purchase_orders} total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-on-surface-variant border-b border-outline-variant">
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide">PO No.</th>
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide">Vendor</th>
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide">Status</th>
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide text-right">Amount</th>
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
            <span className="text-label-bold text-on-surface-variant">{stats.invoices} total</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-container-low text-on-surface-variant border-b border-outline-variant">
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide">Invoice No.</th>
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide">Vendor</th>
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide">Status</th>
                  <th className="px-4 py-2.5 text-label-bold font-semibold uppercase tracking-wide text-right">Amount</th>
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
    </div>
  );
}
