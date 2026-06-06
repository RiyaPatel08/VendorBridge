import { useEffect, useState } from "react";
import { Layout } from "./components/Layout";
import { ActivityPage } from "./features/activity/ActivityPage";
import { ApprovalsPage } from "./features/approvals/ApprovalsPage";
import { AuthPage } from "./features/auth/AuthPage";
import { useAuth } from "./features/auth/AuthContext";
import { Dashboard } from "./features/dashboard/Dashboard";
import { InvoicesPage } from "./features/documents/InvoicesPage";
import { PurchaseOrdersPage } from "./features/documents/PurchaseOrdersPage";
import { QuotationsPage } from "./features/quotations/QuotationsPage";
import { ReportsPage } from "./features/reports/ReportsPage";
import { RfqsPage } from "./features/rfqs/RfqsPage";
import { VendorsPage } from "./features/vendors/VendorsPage";
import { api } from "./lib/api";
import { canAccessView, defaultViewForRole, ROLE_VIEWS, type ViewKey } from "./lib/permissions";
import type { UserRole } from "./lib/types";

export function App() {
  const { token, user, loading } = useAuth();
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");
  const [pendingApprovals, setPendingApprovals] = useState<number>(0);

  const role = (user?.role ?? "vendor") as UserRole;
  const allowedViews = ROLE_VIEWS[role] ?? ROLE_VIEWS.vendor;

  function handleViewChange(view: ViewKey) {
    if (canAccessView(role, view)) {
      setActiveView(view);
    }
  }

  useEffect(() => {
    if (!token || !canAccessView(role, "approvals")) {
      setPendingApprovals(0);
      return;
    }
    api
      .approvals(token)
      .then((list) => setPendingApprovals(list.filter((a) => a.status === "pending").length))
      .catch(() => {});
  }, [token, role, activeView]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="glass-panel rounded-xl px-8 py-6 text-sm font-semibold text-on-surface-variant">
          Loading VendorBridge…
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return <AuthPage />;
  }

  const safeView = allowedViews.includes(activeView) ? activeView : defaultViewForRole(role);

  return (
    <Layout activeView={safeView} onViewChange={handleViewChange} pendingApprovals={pendingApprovals}>
      {safeView === "dashboard" && <Dashboard token={token} />}
      {safeView === "vendors" && <VendorsPage token={token} />}
      {safeView === "rfqs" && <RfqsPage token={token} />}
      {safeView === "quotations" && <QuotationsPage token={token} />}
      {safeView === "approvals" && <ApprovalsPage token={token} />}
      {safeView === "purchaseOrders" && <PurchaseOrdersPage token={token} />}
      {safeView === "invoices" && <InvoicesPage token={token} />}
      {safeView === "reports" && <ReportsPage token={token} />}
      {safeView === "activity" && <ActivityPage token={token} />}
    </Layout>
  );
}
