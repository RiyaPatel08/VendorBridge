import { Check, FilePlus2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../../lib/api";
import type { Approval, ApprovalListItem } from "../../lib/types";

export function ApprovalsPage({ token }: { token: string }) {
  const { user } = useAuth();
  const canApprove = user?.role === "manager" || user?.role === "finance_manager";
  const canGeneratePo = user?.role === "manager" || user?.role === "finance_manager" || user?.role === "procurement_officer";
  const [approvals, setApprovals] = useState<ApprovalListItem[]>([]);
  const [selected, setSelected] = useState<Approval | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    const rows = await api.approvals(token);
    setApprovals(rows);
    if (rows[0]) {
      setSelected(await api.approval(token, rows[0].id));
    }
  }

  useEffect(() => {
    load().catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load approvals"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function decide(kind: "approve" | "reject") {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const remarks = kind === "approve" ? "Approved for procurement." : "Rejected with remarks.";
      const result = kind === "approve" ? await api.approve(token, selected.id, remarks) : await api.reject(token, selected.id, remarks);
      setSelected(result);
      setNotice(`Approval ${kind}d`);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not update approval");
    } finally {
      setBusy(false);
    }
  }

  async function generatePo() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      const po = await api.generatePo(token, selected.id);
      setNotice(`Generated ${po.po_number}`);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not generate PO");
    } finally {
      setBusy(false);
    }
  }

  const budget = selected?.budget_impact;

  return (
    <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
      <section className="panel overflow-hidden">
        <div className="border-b border-line p-4"><h2 className="font-semibold">Approval Queue</h2></div>
        <div className="divide-y divide-line">
          {approvals.map((approval) => (
            <button
              key={approval.id}
              className="block w-full px-4 py-3 text-left hover:bg-slate-50"
              onClick={async () => setSelected(await api.approval(token, approval.id))}
            >
              <p className="font-semibold">{approval.rfq_title}</p>
              <p className="mt-1 text-sm text-slate-600">{approval.vendor_name} · INR {Number(approval.quote_total).toLocaleString("en-IN")}</p>
              <p className="mt-1 text-xs uppercase text-slate-500">{approval.status} · {approval.risk_tier ?? "risk pending"}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="panel p-4">
        {error && <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
        {notice && <div className="mb-3 rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}
        {selected ? (
          <div className="space-y-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 className="text-lg font-semibold">{selected.rfq_title}</h2>
                <p className="text-sm text-slate-600">{selected.vendor_name} · INR {Number(selected.quote_total).toLocaleString("en-IN")}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${selected.risk_tier === "low" ? "bg-teal-50 text-success" : selected.risk_tier === "medium" ? "bg-amber-50 text-warn" : "bg-red-50 text-danger"}`}>
                {selected.risk_tier ?? "pending"} risk
              </span>
            </div>

            {budget && (
              <div className="grid gap-3 md:grid-cols-4">
                <Metric label="Budget" value={budget.budget} />
                <Metric label="Spent" value={budget.spent} />
                <Metric label="This PO" value={budget.po_amount} />
                <Metric label="After Approval" value={budget.remaining_after} />
              </div>
            )}

            <div>
              <p className="label mb-2">Policy reasons</p>
              <div className="flex flex-wrap gap-2">
                {(selected.policy_reasons?.length ? selected.policy_reasons : ["No blocking policy reasons"]).map((reason) => (
                  <span key={reason} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{reason}</span>
                ))}
              </div>
            </div>

            <div>
              <p className="label mb-2">Timeline</p>
              <div className="space-y-2">
                {selected.steps.map((step) => (
                  <div key={step.id} className="rounded-md border border-line p-3 text-sm">
                    <p className="font-semibold">L{step.sequence}: {step.approver_name}</p>
                    <p className="text-slate-600">{step.status}{step.remarks ? ` · ${step.remarks}` : ""}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {canApprove && (
                <>
                  <button className="btn-primary" disabled={busy || selected.status !== "pending"} onClick={() => decide("approve")}><Check size={18} /> Approve</button>
                  <button className="btn-danger" disabled={busy || selected.status !== "pending"} onClick={() => decide("reject")}><X size={18} /> Reject</button>
                </>
              )}
              {canGeneratePo && (
                <button className="btn-secondary" disabled={busy || selected.status !== "approved"} onClick={generatePo}><FilePlus2 size={18} /> Generate PO</button>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">No approval selected.</p>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-line bg-field p-3">
      <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
      <p className="mt-2 font-semibold">INR {Number(value ?? 0).toLocaleString("en-IN")}</p>
    </div>
  );
}

