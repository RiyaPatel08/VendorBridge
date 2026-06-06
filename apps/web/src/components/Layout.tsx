import {
  Activity,
  BarChart3,
  Bell,
  ClipboardList,
  FileText,
  Home,
  LogOut,
  ReceiptIndianRupee,
  ShieldCheck,
  ShoppingCart,
  Store,
  Users,
} from "lucide-react";
import { roleLabel } from "../lib/format";
import { useAuth } from "../features/auth/AuthContext";

export type ViewKey = "dashboard" | "vendors" | "activity";

const navItems = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "vendors", label: "Vendors", icon: Store },
  { key: "activity", label: "Activity", icon: Activity },
] satisfies { key: ViewKey; label: string; icon: typeof Home }[];

const plannedItems = [
  { label: "RFQs", icon: ClipboardList },
  { label: "Quotations", icon: FileText },
  { label: "Approvals", icon: ShieldCheck },
  { label: "Purchase Orders", icon: ShoppingCart },
  { label: "Invoices", icon: ReceiptIndianRupee },
  { label: "Reports", icon: BarChart3 },
];

export function Layout({
  activeView,
  onViewChange,
  children,
}: {
  activeView: ViewKey;
  onViewChange: (view: ViewKey) => void;
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100 text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-800 bg-ink text-white lg:block">
        <div className="flex h-full flex-col">
          <div className="border-b border-slate-800 px-5 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-cyan-600 font-bold">
                VB
              </div>
              <div>
                <p className="font-semibold">VendorBridge</p>
                <p className="text-xs text-slate-400">Procurement ERP</p>
              </div>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navItems.map((item) => (
              <button
                key={item.key}
                className={`flex h-10 w-full items-center gap-3 rounded-md px-3 text-left text-sm font-medium transition ${
                  activeView === item.key ? "bg-cyan-700 text-white" : "text-slate-300 hover:bg-slate-800"
                }`}
                onClick={() => onViewChange(item.key)}
              >
                <item.icon size={18} />
                {item.label}
              </button>
            ))}
            <div className="pt-3">
              {plannedItems.map((item) => (
                <div
                  key={item.label}
                  className="flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-slate-500"
                >
                  <item.icon size={18} />
                  {item.label}
                </div>
              ))}
            </div>
          </nav>
          <div className="border-t border-slate-800 p-3">
            <button
              className="flex h-10 w-full items-center gap-3 rounded-md px-3 text-sm font-medium text-slate-300 hover:bg-slate-800"
              onClick={logout}
            >
              <LogOut size={18} />
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-line bg-white">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 py-3 sm:px-6">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase text-slate-500">VendorBridge</p>
              <h1 className="truncate text-lg font-semibold text-ink">
                {activeView === "dashboard" ? "Dashboard" : activeView === "vendors" ? "Vendors" : "Activity"}
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <button className="btn-secondary h-9 w-9 px-0" title="Notifications">
                <Bell size={18} />
              </button>
              <div className="hidden items-center gap-3 rounded-md border border-line px-3 py-2 sm:flex">
                <Users size={18} className="text-slate-500" />
                <div className="text-right">
                  <p className="text-sm font-semibold leading-none">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{user ? roleLabel(user.role) : ""}</p>
                </div>
              </div>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-4 pb-3 lg:hidden">
            {navItems.map((item) => (
              <button
                key={item.key}
                className={`btn h-9 shrink-0 ${
                  activeView === item.key ? "bg-brand text-white" : "border border-line bg-white text-ink"
                }`}
                onClick={() => onViewChange(item.key)}
              >
                <item.icon size={16} />
                {item.label}
              </button>
            ))}
          </nav>
        </header>
        <main className="px-4 py-5 sm:px-6">{children}</main>
      </div>
    </div>
  );
}

