import { Activity, CheckCircle2, FileStack, IndianRupee, Store, Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";
import type { DashboardStats } from "../../lib/types";

const initialStats: DashboardStats = {
  vendors: 0,
  active_vendors: 0,
  rfqs: 0,
  purchase_orders: 0,
  invoices: 0,
  ledger_entries: 0,
};

export function Dashboard({ token }: { token: string }) {
  const [stats, setStats] = useState<DashboardStats>(initialStats);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboardStats(token)
      .then(setStats)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load dashboard"));
  }, [token]);

  const cards = [
    { label: "Active Vendors", value: stats.active_vendors, icon: Store, accent: "text-success" },
    { label: "Total Vendors", value: stats.vendors, icon: CheckCircle2, accent: "text-brand" },
    { label: "RFQs", value: stats.rfqs, icon: Workflow, accent: "text-blue-700" },
    { label: "Ledger Entries", value: stats.ledger_entries, icon: Activity, accent: "text-warn" },
  ];

  return (
    <div className="space-y-5">
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="panel p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm text-slate-600">{card.label}</p>
                <p className="mt-2 text-2xl font-semibold">{card.value}</p>
              </div>
              <card.icon className={card.accent} size={26} />
            </div>
          </div>
        ))}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2">
            <Workflow size={20} className="text-brand" />
            <h2 className="font-semibold">Process Map</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-5">
            {["RFQ", "Quotes", "Approval", "PO", "Invoice"].map((step, index) => (
              <div key={step} className="rounded-md border border-line bg-field p-3 text-center">
                <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-white text-sm font-semibold text-brand ring-1 ring-line">
                  {index + 1}
                </div>
                <p className="text-sm font-semibold">{step}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="panel p-4">
          <div className="mb-4 flex items-center gap-2">
            <IndianRupee size={20} className="text-success" />
            <h2 className="font-semibold">Documents</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-line p-3">
              <p className="text-sm text-slate-600">Purchase Orders</p>
              <p className="mt-2 text-2xl font-semibold">{stats.purchase_orders}</p>
            </div>
            <div className="rounded-md border border-line p-3">
              <p className="text-sm text-slate-600">Invoices</p>
              <p className="mt-2 text-2xl font-semibold">{stats.invoices}</p>
            </div>
          </div>
          <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
            <FileStack className="mr-2 inline text-slate-500" size={16} />
            Recent procurement documents will appear here.
          </div>
        </div>
      </section>
    </div>
  );
}
