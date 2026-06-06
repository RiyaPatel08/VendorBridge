import type { LifecycleStage, VendorStatus } from "../lib/types";

const statusClasses: Record<VendorStatus, string> = {
  active: "bg-secondary/10 text-secondary border border-secondary/20",
  pending: "bg-primary-container/30 text-primary border border-primary/20",
  blocked: "bg-error-container text-on-error-container border border-error/20",
};

const stageClasses: Record<LifecycleStage, string> = {
  potential: "bg-surface-container text-on-surface-variant border border-outline-variant",
  emerging: "bg-[#7cf2ee]/30 text-[#006a68] border border-[#006a68]/20",
  verified: "bg-primary/10 text-primary border border-primary/20",
  trusted: "bg-secondary/10 text-secondary border border-secondary/20",
  preferred: "bg-tertiary/10 text-tertiary border border-tertiary/20",
};

const stageLabels: Record<LifecycleStage, string> = {
  potential: "Potential",
  emerging: "Emerging",
  verified: "Verified",
  trusted: "Trusted",
  preferred: "Preferred",
};

export function StatusBadge({ status }: { status: VendorStatus }) {
  const labels: Record<VendorStatus, string> = {
    active: "Active",
    pending: "Pending",
    blocked: "Blocked",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusClasses[status]}`}>
      {labels[status]}
    </span>
  );
}

export function StageBadge({ stage }: { stage: LifecycleStage }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${stageClasses[stage]}`}>
      {stageLabels[stage]}
    </span>
  );
}

export function ComplianceBadge({ value }: { value: "compliant" | "needs_review" | "blocked" }) {
  const classes =
    value === "compliant"
      ? "bg-secondary/10 text-secondary border border-secondary/20"
      : value === "blocked"
        ? "bg-error-container text-on-error-container border border-error/20"
        : "bg-primary-container/30 text-primary border border-primary/20";
  const labels: Record<typeof value, string> = {
    compliant: "Compliant",
    needs_review: "Needs Review",
    blocked: "Blocked",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${classes}`}>
      {labels[value]}
    </span>
  );
}
