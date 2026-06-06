import { Download, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ApiError } from "../../lib/api";
import type { ReportsSummary } from "../../lib/types";

const CATEGORY_COLORS = ["#6d4262", "#006a68", "#005d1e", "#875a7b", "#ba1a1a", "#80747b", "#b45309"];

const LIFECYCLE_COLORS: Record<string, string> = {
  potential: "#80747b",
  emerging: "#60d9d5",
  verified: "#6d4262",
  trusted: "#006a68",
  preferred: "#005d1e",
};

export function ReportsPage({ token }: { token: string }) {
  const [summary, setSummary] = useState<ReportsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reports(token)
      .then(setSummary)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load reports"));
  }, [token]);

  async function exportCsv() {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"}/reports/export.csv`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "vendorbridge-report.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  const radarData = summary?.vendors.length
    ? [
        { dimension: "Rating", ...Object.fromEntries(summary.vendors.slice(0, 4).map((v) => [v.name, (v.rating / 5) * 100])) },
        { dimension: "Reliability", ...Object.fromEntries(summary.vendors.slice(0, 4).map((v) => [v.name, v.reliability_score ?? 0])) },
        { dimension: "Delivery", ...Object.fromEntries(summary.vendors.slice(0, 4).map((v) => [v.name, v.delivery_score ?? 0])) },
        { dimension: "Orders", ...Object.fromEntries(summary.vendors.slice(0, 4).map((v) => [v.name, Math.min(100, (v.completed_orders_count / 40) * 100)])) },
      ]
    : [];

  const radarVendors = summary?.vendors.slice(0, 4) ?? [];
  const radarColors = ["#6d4262", "#006a68", "#005d1e", "#875a7b"];

  return (
    <div className="space-y-5">
      {error && (
        <div className="rounded-lg bg-error-container border border-error/20 px-4 py-3 text-sm text-on-error-container">
          {error}
        </div>
      )}

      {/* KPI Row */}
      <section className="grid gap-4 md:grid-cols-4">
        <Kpi label="Total Spend" value={`₹${Number(summary?.kpis.total_spend ?? 0).toLocaleString("en-IN")}`} icon="💰" />
        <Kpi label="Pending Approvals" value={summary?.kpis.pending_approvals ?? 0} icon="⏳" />
        <Kpi label="RFQs" value={summary?.kpis.rfqs ?? 0} icon="📋" />
        <Kpi label="Quotations" value={summary?.kpis.quotations ?? 0} icon="💬" />
      </section>

      {/* Monthly Spend + Category Pie */}
      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        {/* Monthly Spend Bar Chart */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={18} className="text-primary" />
              <h2 className="font-title-sm text-title-sm text-on-surface">Monthly Spend</h2>
            </div>
            <button className="btn-secondary h-9" onClick={exportCsv}><Download size={16} /> Export</button>
          </div>
          <div className="p-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary?.monthly_spend ?? []}>
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6d4262" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#875a7b" stopOpacity={0.6} />
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
                <Bar dataKey="spend" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Spend Pie Chart */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
            <h2 className="font-title-sm text-title-sm text-on-surface">Spend by Category</h2>
            <p className="text-label-sm text-on-surface-variant mt-0.5">Procurement distribution</p>
          </div>
          <div className="p-4 h-72">
            {summary?.categories.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={summary.categories.filter((c) => c.spend > 0)}
                    dataKey="spend"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                    strokeWidth={2}
                    stroke="#fff"
                    label={({ category, percent }: { category: string; percent: number }) =>
                      `${category} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={{ stroke: "#80747b", strokeWidth: 1 }}
                  >
                    {summary.categories
                      .filter((c) => c.spend > 0)
                      .map((_entry, i) => (
                        <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                      ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "#fff",
                      border: "1px solid #d2c2ca",
                      borderRadius: "8px",
                      fontSize: "13px",
                    }}
                    formatter={(value: number) => [`₹${value.toLocaleString("en-IN")}`, "Spend"]}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-on-surface-variant text-sm">
                No category spending data yet
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Vendor Performance Radar + Vendor Cards */}
      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        {/* Vendor Performance Radar */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
            <h2 className="font-title-sm text-title-sm text-on-surface">Vendor Performance Radar</h2>
            <p className="text-label-sm text-on-surface-variant mt-0.5">Top vendors across key dimensions</p>
          </div>
          <div className="p-4 h-80">
            {radarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} outerRadius="75%">
                  <PolarGrid stroke="#d2c2ca" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "#4e444a", fontWeight: 600 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: "#80747b" }} />
                  {radarVendors.map((vendor, i) => (
                    <Radar
                      key={vendor.id}
                      name={vendor.name}
                      dataKey={vendor.name}
                      stroke={radarColors[i % radarColors.length]}
                      fill={radarColors[i % radarColors.length]}
                      fillOpacity={0.12}
                      strokeWidth={2}
                    />
                  ))}
                  <Legend
                    verticalAlign="bottom"
                    formatter={(value: string) => (
                      <span className="text-xs font-semibold text-on-surface-variant">{value}</span>
                    )}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#fff",
                      border: "1px solid #d2c2ca",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-on-surface-variant text-sm">
                No vendor data yet
              </div>
            )}
          </div>
        </div>

        {/* Vendor Performance Cards */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
            <h2 className="font-title-sm text-title-sm text-on-surface">Vendor Scorecards</h2>
            <p className="text-label-sm text-on-surface-variant mt-0.5">Individual performance metrics</p>
          </div>
          <div className="p-4 space-y-3 max-h-[340px] overflow-y-auto">
            {summary?.vendors.map((vendor) => (
              <div key={vendor.id} className="rounded-xl border border-outline-variant p-4 hover:border-primary/30 transition-colors">
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs">
                      {vendor.name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-semibold text-on-surface text-sm">{vendor.name}</p>
                      <p className="text-[10px] text-on-surface-variant uppercase font-semibold">
                        <span className={`inline-block px-1.5 py-px rounded border text-[9px] ${
                          LIFECYCLE_COLORS[vendor.lifecycle_stage] ? `border-[${LIFECYCLE_COLORS[vendor.lifecycle_stage]}]/20` : "border-outline-variant"
                        }`}>
                          {vendor.lifecycle_stage}
                        </span>
                        <span className="ml-1.5">{vendor.completed_orders_count} orders</span>
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-on-surface">{vendor.rating.toFixed(1)}</p>
                    <p className="text-[10px] text-on-surface-variant">/ 5.0</p>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold text-on-surface-variant w-16 text-right">Reliability</span>
                    <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden">
                      <div className="h-full rounded-full bg-secondary transition-all" style={{ width: `${vendor.reliability_score ?? 0}%` }} />
                    </div>
                    <span className="text-[10px] font-bold text-on-surface w-8">{(vendor.reliability_score ?? 0).toFixed(0)}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold text-on-surface-variant w-16 text-right">Delivery</span>
                    <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden">
                      <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${vendor.delivery_score ?? 0}%` }} />
                    </div>
                    <span className="text-[10px] font-bold text-on-surface w-8">{(vendor.delivery_score ?? 0).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
            {!summary?.vendors.length && (
              <p className="text-center text-on-surface-variant text-sm py-8">No vendor data yet.</p>
            )}
          </div>
        </div>
      </section>

      {/* Category Detail Cards */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
          <h2 className="font-title-sm text-title-sm text-on-surface">Category Overview</h2>
        </div>
        <div className="p-4 grid gap-3 md:grid-cols-3">
          {summary?.categories.map((category, i) => (
            <div key={category.category} className="rounded-xl border border-outline-variant p-4 hover:border-primary/30 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }} />
                <p className="font-semibold text-on-surface text-sm">{category.category}</p>
              </div>
              <p className="text-on-surface-variant text-xs">{category.vendors} vendors</p>
              <p className="mt-2 text-lg font-bold text-on-surface">₹{category.spend.toLocaleString("en-IN")}</p>
            </div>
          ))}
          {!summary?.categories.length && <p className="text-sm text-on-surface-variant col-span-3 text-center py-4">No category data yet.</p>}
        </div>
      </section>
    </div>
  );
}

function Kpi({ label, value, icon }: { label: string; value: string | number; icon: string }) {
  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-card">
      <div className="flex items-center justify-between">
        <p className="text-label-bold text-on-surface-variant uppercase tracking-wider">{label}</p>
        <span className="text-lg">{icon}</span>
      </div>
      <p className="mt-2 font-display-lg text-display-lg text-on-surface">{value}</p>
    </div>
  );
}
