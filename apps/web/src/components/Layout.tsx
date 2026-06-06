import {
  Activity,
  BarChart3,
  Bell,
  ChevronDown,
  ClipboardList,
  FileText,
  Home,
  LogOut,
  Menu,
  ReceiptIndianRupee,
  ShieldCheck,
  ShoppingCart,
  Store,
  X,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../features/auth/AuthContext";
import { ROLE_VIEWS, roleBadgeColor, roleLabel, type ViewKey } from "../lib/permissions";
import type { UserRole } from "../lib/types";

type NavItem = { key: ViewKey; label: string; icon: typeof Home };

const ALL_NAV_ITEMS: NavItem[] = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "vendors", label: "Vendors", icon: Store },
  { key: "rfqs", label: "RFQs", icon: ClipboardList },
  { key: "quotations", label: "Quotations", icon: FileText },
  { key: "approvals", label: "Approvals", icon: ShieldCheck },
  { key: "purchaseOrders", label: "Purchase Orders", icon: ShoppingCart },
  { key: "invoices", label: "Invoices", icon: ReceiptIndianRupee },
  { key: "reports", label: "Reports", icon: BarChart3 },
  { key: "activity", label: "Activity", icon: Activity },
];

export function Layout({
  activeView,
  onViewChange,
  pendingApprovals,
  children,
}: {
  activeView: ViewKey;
  onViewChange: (view: ViewKey) => void;
  pendingApprovals?: number;
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const role = (user?.role ?? "vendor") as UserRole;
  const allowedKeys = ROLE_VIEWS[role] ?? ROLE_VIEWS.vendor;
  const navItems = ALL_NAV_ITEMS.filter((item) => allowedKeys.includes(item.key));
  const showApprovalBadge = allowedKeys.includes("approvals") && pendingApprovals && pendingApprovals > 0;

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      <div className="px-4 py-5 border-b border-outline-variant">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-on-primary text-sm font-bold">
            VB
          </div>
          <div>
            <h1 className="font-bold text-primary text-base leading-tight">VendorBridge</h1>
            <p className="text-[10px] text-on-surface-variant uppercase tracking-wider">Enterprise Procurement</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 flex flex-col gap-0.5">
        {navItems.map((item) => {
          const isActive = activeView === item.key;
          const hasBadge = item.key === "approvals" && showApprovalBadge;
          return (
            <button
              key={item.key}
              className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-left text-body-base transition-colors duration-150 ${
                isActive
                  ? "bg-secondary-container text-on-secondary-container font-semibold"
                  : "text-on-surface-variant hover:bg-surface-container-high"
              }`}
              onClick={() => {
                onViewChange(item.key);
                setMobileSidebarOpen(false);
              }}
            >
              <item.icon size={20} className="shrink-0" />
              <span className="flex-1">{item.label}</span>
              {hasBadge && (
                <span className="bg-error text-on-error text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  {pendingApprovals}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {role === "procurement_officer" && (
        <div className="px-3 pb-3 pt-2 border-t border-outline-variant">
          <button
            className="w-full bg-primary text-on-primary py-2.5 rounded-lg font-semibold text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            onClick={() => {
              onViewChange("rfqs");
              setMobileSidebarOpen(false);
            }}
          >
            + Create RFQ
          </button>
        </div>
      )}

      <div className="px-2 py-2 border-t border-outline-variant">
        <button
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors text-sm"
          onClick={logout}
        >
          <LogOut size={18} />
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <aside className="fixed inset-y-0 left-0 hidden lg:flex w-sidebar_width bg-surface-container-lowest border-r border-outline-variant shadow-sm z-30 flex-col">
        <SidebarContent />
      </aside>

      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div
            className="fixed inset-0 bg-inverse-surface/40"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <aside className="relative flex w-sidebar_width flex-col bg-surface-container-lowest shadow-xl">
            <button
              className="absolute top-4 right-3 p-1.5 rounded-lg text-on-surface-variant hover:bg-surface-container-high"
              onClick={() => setMobileSidebarOpen(false)}
            >
              <X size={20} />
            </button>
            <SidebarContent />
          </aside>
        </div>
      )}

      <div className="lg:ml-sidebar_width flex flex-col min-h-screen">
        <header className="sticky top-0 z-20 h-topbar_height bg-surface-container-lowest border-b border-outline-variant flex items-center justify-between px-4 gap-4">
          <button
            className="lg:hidden p-2 rounded-lg text-on-surface-variant hover:bg-surface-container-high"
            onClick={() => setMobileSidebarOpen(true)}
          >
            <Menu size={22} />
          </button>

          <div className="hidden md:flex flex-1 max-w-md relative items-center">
            <svg
              className="absolute left-3 text-on-surface-variant pointer-events-none w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input
              className="w-full bg-surface-container border border-outline-variant rounded-lg pl-10 pr-4 py-2 text-sm text-on-surface focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-colors"
              placeholder="Search across ERP..."
              readOnly
            />
          </div>

          <div className="flex-1 md:hidden">
            <p className="text-sm font-semibold text-on-surface">
              {navItems.find((i) => i.key === activeView)?.label ?? "VendorBridge"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button className="relative p-2 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors">
              <Bell size={20} />
              {showApprovalBadge ? (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-error rounded-full ring-2 ring-surface-container-lowest" />
              ) : null}
            </button>
            <div className="hidden sm:flex h-8 w-px bg-outline-variant" />
            <div className="relative">
              <button
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-surface-container-high transition-colors"
                onClick={() => setUserMenuOpen((v) => !v)}
              >
                <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-sm">
                  {user?.first_name?.charAt(0) ?? "U"}
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-semibold text-on-surface leading-tight">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-[11px] text-on-surface-variant leading-tight">
                    <span className={`inline-block px-1.5 py-px rounded border text-[10px] font-bold ${roleBadgeColor(role)}`}>
                      {roleLabel(role)}
                    </span>
                  </p>
                </div>
                <ChevronDown size={16} className="text-on-surface-variant hidden sm:block" />
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card z-50 overflow-hidden">
                  <div className="px-4 py-3 border-b border-outline-variant">
                    <p className="text-sm font-semibold text-on-surface">{user?.first_name} {user?.last_name}</p>
                    <p className="text-xs text-on-surface-variant">{user?.email}</p>
                  </div>
                  <button
                    className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-on-surface-variant hover:bg-surface-container-high transition-colors"
                    onClick={() => {
                      setUserMenuOpen(false);
                      logout();
                    }}
                  >
                    <LogOut size={16} />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 p-container_padding">{children}</main>

        <div className="bg-surface-container-lowest border-t border-outline-variant px-6 py-2 flex items-center justify-between text-xs text-on-surface-variant">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-tertiary inline-block" />
              System Online
            </span>
          </div>
          <span>VendorBridge IQ - BuzzBeatStrong</span>
        </div>
      </div>
    </div>
  );
}
