import { Download } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ApiError } from "../../lib/api";
import type { ReportsSummary } from "../../lib/types";

export function ReportsPage({ token }: { token: string }) {
  const [summary, setSummary] = useState<ReportsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reports(token)
      .then(setSummary)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load reports"));
  }, [token]);

  async function exportCsv() {
    const response = await fetch("http://localhost:8000/api/v1/reports/export.csv", {
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

  return (
    <div className="space-y-5">
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
      <section className="grid gap-4 md:grid-cols-4">
        <Kpi label="Total Spend" value={`INR ${Number(summary?.kpis.total_spend ?? 0).toLocaleString("en-IN")}`} />
        <Kpi label="Pending Approvals" value={summary?.kpis.pending_approvals ?? 0} />
        <Kpi label="RFQs" value={summary?.kpis.rfqs ?? 0} />
        <Kpi label="Quotations" value={summary?.kpis.quotations ?? 0} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="font-semibold">Monthly Spend</h2>
            <button className="btn-secondary h-9" onClick={exportCsv}><Download size={16} /> Export</button>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary?.monthly_spend ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="spend" fill="#155e75" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="panel p-4">
          <h2 className="mb-4 font-semibold">Vendor Performance</h2>
          <div className="space-y-3">
            {summary?.vendors.map((vendor) => (
              <div key={vendor.id} className="rounded-md border border-line p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{vendor.name}</p>
                  <p className="text-sm text-slate-600">{vendor.rating.toFixed(1)} / 5</p>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-100">
                  <div className="h-2 rounded-full bg-success" style={{ width: `${vendor.reliability_score}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-500">{vendor.lifecycle_stage} | {vendor.completed_orders_count} orders</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel p-4">
        <h2 className="mb-4 font-semibold">Spend by Category</h2>
        <div className="grid gap-3 md:grid-cols-3">
          {summary?.categories.map((category) => (
            <div key={category.category} className="rounded-md border border-line p-3">
              <p className="font-semibold">{category.category}</p>
              <p className="mt-1 text-sm text-slate-600">{category.vendors} vendors</p>
              <p className="mt-3 text-lg font-semibold">INR {category.spend.toLocaleString("en-IN")}</p>
            </div>
          ))}
          {!summary?.categories.length && <p className="text-sm text-slate-500">No category data yet.</p>}
        </div>
      </section>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="panel p-4">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-2 text-xl font-semibold">{value}</p>
    </div>
  );
}
