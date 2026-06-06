import { useState } from "react";
import { Layout, type ViewKey } from "./components/Layout";
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

export function App() {
  const { token, user, loading } = useAuth();
  const [activeView, setActiveView] = useState<ViewKey>("dashboard");

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="panel p-5 text-sm font-semibold text-slate-600">Loading VendorBridge...</div>
      </div>
    );
  }

  if (!token || !user) {
    return <AuthPage />;
  }

  return (
    <Layout activeView={activeView} onViewChange={setActiveView}>
      {activeView === "dashboard" && <Dashboard token={token} />}
      {activeView === "vendors" && <VendorsPage token={token} />}
      {activeView === "rfqs" && <RfqsPage token={token} />}
      {activeView === "quotations" && <QuotationsPage token={token} />}
      {activeView === "approvals" && <ApprovalsPage token={token} />}
      {activeView === "purchaseOrders" && <PurchaseOrdersPage token={token} />}
      {activeView === "invoices" && <InvoicesPage token={token} />}
      {activeView === "reports" && <ReportsPage token={token} />}
      {activeView === "activity" && <ActivityPage token={token} />}
    </Layout>
  );
}
