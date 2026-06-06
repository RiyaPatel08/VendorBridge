import type { LifecycleStage, VendorStatus } from "../lib/types";
import { stageLabel } from "../lib/format";

const statusClasses: Record<VendorStatus, string> = {
  active: "bg-teal-50 text-success ring-teal-200",
  pending: "bg-amber-50 text-warn ring-amber-200",
  blocked: "bg-red-50 text-danger ring-red-200",
};

const stageClasses: Record<LifecycleStage, string> = {
  potential: "bg-slate-100 text-slate-700 ring-slate-200",
  emerging: "bg-cyan-50 text-cyan-700 ring-cyan-200",
  verified: "bg-blue-50 text-blue-700 ring-blue-200",
  trusted: "bg-teal-50 text-success ring-teal-200",
  preferred: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export function StatusBadge({ status }: { status: VendorStatus }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ${statusClasses[status]}`}>
      {stageLabel(status)}
    </span>
  );
}

export function StageBadge({ stage }: { stage: LifecycleStage }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ${stageClasses[stage]}`}>
      {stageLabel(stage)}
    </span>
  );
}

export function ComplianceBadge({ value }: { value: "compliant" | "needs_review" | "blocked" }) {
  const classes =
    value === "compliant"
      ? "bg-teal-50 text-success ring-teal-200"
      : value === "blocked"
        ? "bg-red-50 text-danger ring-red-200"
        : "bg-amber-50 text-warn ring-amber-200";
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ring-1 ${classes}`}>
      {value === "needs_review" ? "Needs Review" : stageLabel(value)}
    </span>
  );
}

