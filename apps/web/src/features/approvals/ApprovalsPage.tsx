import { Check, ChevronRight, FilePlus2, ShieldCheck, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../../lib/api";
import { can } from "../../lib/permissions";
import type { Approval, ApprovalListItem } from "../../lib/types";

const RISK_COLORS: Record<string, string> = {
  low: "bg-secondary/10 text-secondary border-secondary/20",
  medium: "bg-primary-container/30 text-primary border-primary/20",
  high: "bg-error-container text-on-error-container border-error/20",
};

const RISK_DIMENSIONS = [
  { key: "verification", label: "Verification", color: "#6d4262" },
  { key: "delivery_reliability", label: "Delivery", color: "#006a68" },
  { key: "inventory_availability", label: "Inventory", color: "#005d1e" },
  { key: "vendor_history", label: "History", color: "#875a7b" },
  { key: "price_abnormality", label: "Price Check", color: "#80747b" },
];

const STEP_STATUS_ICON: Record<string, { bg: string; icon: React.ReactNode }> = {
  approved: {
    bg: "bg-secondary text-on-secondary",
    icon: <Check size={14} />,
  },
  rejected: {
    bg: "bg-error text-on-error",
    icon: <X size={14} />,
  },
  pending: {
    bg: "bg-surface-container-high text-on-surface-variant",
    icon: <span className="w-2 h-2 rounded-full bg-on-surface-variant" />,
  },
};

function RiskBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] font-semibold text-on-surface-variant w-20 text-right truncate">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-surface-container-high overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, value)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[11px] font-bold text-on-surface w-10">{value.toFixed(0)}%</span>
    </div>
  );
}

function BudgetHealthBar({ budget }: { budget: Record<string, number | string> }) {
  const total = Number(budget.budget) || 1;
  const spent = Number(budget.spent) || 0;
  const poAmount = Number(budget.po_amount) || 0;
  const remaining = Number(budget.remaining_after) || 0;
  const spentPct = Math.min(100, (spent / total) * 100);
  const poPct = Math.min(100 - spentPct, (poAmount / total) * 100);
  const health = budget.health as string;
  const healthColor = health === "green" ? "bg-secondary" : health === "yellow" ? "bg-[#b45309]" : "bg-error";

  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 shadow-card">
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-2.5 h-2.5 rounded-full ${healthColor}`} />
        <h4 className="text-label-bold text-on-surface uppercase tracking-wider">Budget Impact — {budget.department}</h4>
      </div>
      <div className="h-4 rounded-full bg-surface-container-high overflow-hidden flex mb-3">
        <div className="h-full bg-on-surface-variant/40 transition-all" style={{ width: `${spentPct}%` }} />
        <div className={`h-full ${healthColor} transition-all`} style={{ width: `${poPct}%` }} />
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        <div>
          <p className="text-[10px] text-on-surface-variant font-semibold uppercase">Budget</p>
          <p className="text-sm font-bold text-on-surface">₹{Number(budget.budget).toLocaleString("en-IN")}</p>
        </div>
        <div>
          <p className="text-[10px] text-on-surface-variant font-semibold uppercase">Spent</p>
          <p className="text-sm font-bold text-on-surface">₹{spent.toLocaleString("en-IN")}</p>
        </div>
        <div>
          <p className="text-[10px] text-on-surface-variant font-semibold uppercase">This PO</p>
          <p className="text-sm font-bold text-primary">₹{poAmount.toLocaleString("en-IN")}</p>
        </div>
        <div>
          <p className="text-[10px] text-on-surface-variant font-semibold uppercase">Remaining</p>
          <p className={`text-sm font-bold ${remaining >= 0 ? "text-secondary" : "text-error"}`}>
            ₹{remaining.toLocaleString("en-IN")}
          </p>
        </div>
      </div>
    </div>
  );
}

export function ApprovalsPage({ token }: { token: string }) {
  const { user } = useAuth();
  const canApprove = can(user?.role, "approvePurchases");
  const canGeneratePo = can(user?.role, "generatePurchaseOrder");
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
  const riskBreakdown = selected?.risk_breakdown;

  return (
    <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
      {/* Approval Queue */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright flex items-center gap-2">
          <ShieldCheck size={18} className="text-primary" />
          <h2 className="font-title-sm text-title-sm text-on-surface">Approval Queue</h2>
        </div>
        <div className="divide-y divide-outline-variant">
          {approvals.map((approval) => {
            const isSelected = selected?.id === approval.id;
            return (
              <button
                key={approval.id}
                className={`block w-full px-4 py-3.5 text-left transition-colors ${isSelected ? "bg-primary/5 border-l-2 border-l-primary" : "hover:bg-surface-container-low border-l-2 border-l-transparent"}`}
                onClick={async () => setSelected(await api.approval(token, approval.id))}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-on-surface text-sm">{approval.rfq_title}</p>
                  <ChevronRight size={14} className="text-on-surface-variant shrink-0" />
                </div>
                <p className="mt-1 text-xs text-on-surface-variant">
                  {approval.vendor_name} · ₹{Number(approval.quote_total).toLocaleString("en-IN")}
                </p>
                <div className="mt-1.5 flex items-center gap-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                    approval.status === "approved" ? "bg-secondary/10 text-secondary border-secondary/20" :
                    approval.status === "rejected" ? "bg-error-container text-on-error-container border-error/20" :
                    "bg-primary-container/30 text-primary border-primary/20"
                  }`}>
                    {approval.status}
                  </span>
                  {approval.risk_tier && (
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${RISK_COLORS[approval.risk_tier] ?? RISK_COLORS.medium}`}>
                      {approval.risk_tier} risk
                    </span>
                  )}
                </div>
              </button>
            );
          })}
          {approvals.length === 0 && (
            <p className="px-4 py-8 text-center text-on-surface-variant text-sm">No approvals in queue.</p>
          )}
        </div>
      </section>

      {/* Detail Panel */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card p-5">
        {error && (
          <div className="mb-4 rounded-lg bg-error-container border border-error/20 px-4 py-3 text-sm text-on-error-container">
            {error}
          </div>
        )}
        {notice && (
          <div className="mb-4 rounded-lg bg-secondary/10 border border-secondary/20 px-4 py-3 text-sm text-secondary font-semibold">
            {notice}
          </div>
        )}
        {selected ? (
          <div className="space-y-5">
            {/* Header */}
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 className="font-title-sm text-title-sm text-on-surface">{selected.rfq_title}</h2>
                <p className="text-body-base text-on-surface-variant mt-0.5">
                  {selected.vendor_name} · ₹{Number(selected.quote_total).toLocaleString("en-IN")}
                </p>
              </div>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold uppercase border ${RISK_COLORS[selected.risk_tier ?? "medium"] ?? RISK_COLORS.medium}`}>
                {selected.risk_tier ?? "pending"} risk
              </span>
            </div>

            {/* Risk Breakdown Bars */}
            {riskBreakdown && (
              <div className="bg-surface-container-low border border-outline-variant rounded-xl p-4">
                <p className="text-label-bold text-on-surface-variant uppercase tracking-wider mb-3">Risk Assessment Breakdown</p>
                <div className="space-y-2">
                  {RISK_DIMENSIONS.map((dim) => (
                    <RiskBar
                      key={dim.key}
                      label={dim.label}
                      value={riskBreakdown[dim.key] ?? 0}
                      color={dim.color}
                    />
                  ))}
                </div>
                <div className="mt-3 pt-3 border-t border-outline-variant flex items-center justify-between">
                  <span className="text-xs font-semibold text-on-surface-variant">Weighted Risk Score</span>
                  <span className="text-sm font-bold text-on-surface">{(riskBreakdown.weighted_score ?? 0).toFixed(1)}%</span>
                </div>
              </div>
            )}

            {/* Budget Impact */}
            {budget && <BudgetHealthBar budget={budget} />}

            {/* Policy Reasons */}
            <div>
              <p className="text-label-bold text-on-surface-variant uppercase tracking-wider mb-2">Policy Reasons</p>
              <div className="flex flex-wrap gap-2">
                {(selected.policy_reasons?.length ? selected.policy_reasons : ["No blocking policy reasons"]).map((reason) => (
                  <span key={reason} className="rounded-full bg-surface-container-high border border-outline-variant px-3 py-1 text-xs font-semibold text-on-surface-variant">
                    {reason}
                  </span>
                ))}
              </div>
            </div>

            {/* Approval Chain Stepper */}
            <div>
              <p className="text-label-bold text-on-surface-variant uppercase tracking-wider mb-3">Approval Chain</p>
              <div className="space-y-0">
                {selected.steps.map((step, i) => {
                  const stepStyle = STEP_STATUS_ICON[step.status] ?? STEP_STATUS_ICON.pending;
                  return (
                    <div key={step.id} className="flex items-start gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center ${stepStyle.bg} shadow-sm`}>
                          {stepStyle.icon}
                        </div>
                        {i < selected.steps.length - 1 && (
                          <div className="w-0.5 h-8 bg-outline-variant" />
                        )}
                      </div>
                      <div className="pb-4 min-w-0">
                        <p className="text-sm font-semibold text-on-surface">
                          L{step.sequence}: {step.approver_name}
                        </p>
                        <p className="text-xs text-on-surface-variant mt-0.5">
                          <span className={`font-bold uppercase ${
                            step.status === "approved" ? "text-secondary" :
                            step.status === "rejected" ? "text-error" :
                            "text-on-surface-variant"
                          }`}>
                            {step.status}
                          </span>
                          {step.remarks && <span> · {step.remarks}</span>}
                        </p>
                        {step.decided_at && (
                          <p className="text-[10px] text-on-surface-variant mt-0.5">
                            {new Date(step.decided_at).toLocaleString("en-IN")}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-2 pt-2 border-t border-outline-variant">
              {canApprove && (
                <>
                  <button className="btn-primary" disabled={busy || selected.status !== "pending"} onClick={() => decide("approve")}>
                    <Check size={18} /> Approve
                  </button>
                  <button className="btn-danger" disabled={busy || selected.status !== "pending"} onClick={() => decide("reject")}>
                    <X size={18} /> Reject
                  </button>
                </>
              )}
              {canGeneratePo && (
                <button className="btn-secondary" disabled={busy || selected.status !== "approved"} onClick={generatePo}>
                  <FilePlus2 size={18} /> Generate PO
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-48 text-on-surface-variant text-sm">
            Select an approval from the queue.
          </div>
        )}
      </section>
    </div>
  );
}
