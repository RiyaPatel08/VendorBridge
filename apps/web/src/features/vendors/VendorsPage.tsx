import { Ban, RotateCcw, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { StageBadge, StatusBadge } from "../../components/Badge";
import { api, ApiError } from "../../lib/api";
import { can } from "../../lib/permissions";
import type { Vendor, VendorCategory, VendorStatus } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

const AVATAR_COLORS = [
  "bg-primary/20 text-primary",
  "bg-secondary/20 text-secondary",
  "bg-tertiary/20 text-tertiary",
  "bg-[#7c5071]/20 text-[#7c5071]",
  "bg-error/10 text-error",
];

type FilterValue = "all" | VendorStatus;

function VendorAvatar({ name }: { name: string }) {
  const initials = name
    .split(" ")
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
  const color = AVATAR_COLORS[name.charCodeAt(0) % AVATAR_COLORS.length];
  return (
    <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold shrink-0 ${color}`}>
      {initials}
    </div>
  );
}

export function VendorsPage({ token }: { token: string }) {
  const { user } = useAuth();
  const canVerify = can(user?.role, "verifyVendors");
  const canManageStatus = can(user?.role, "manageVendorStatus");
  const showActions = canVerify || canManageStatus;
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [categories, setCategories] = useState<VendorCategory[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<FilterValue>("all");
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const categoryById = useMemo(
    () => new Map(categories.map((category) => [category.id, category.name])),
    [categories],
  );

  async function loadVendors() {
    const params = new URLSearchParams({ page: "1", page_size: "50" });
    if (search.trim()) params.set("search", search.trim());
    if (statusFilter !== "all") params.set("status", statusFilter);
    const response = await api.vendors(token, params);
    setVendors(response.items);
    setTotal(response.total);
  }

  useEffect(() => {
    api
      .categories(token)
      .then(setCategories)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load categories"));
  }, [token]);

  useEffect(() => {
    loadVendors().catch((caught) =>
      setError(caught instanceof ApiError ? caught.message : "Could not load vendors"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, statusFilter]);

  async function handleVerify(vendor: Vendor) {
    setBusy(true);
    setError(null);
    try {
      await api.verifyVendor(token, vendor.id);
      setNotice(`${vendor.name} verified and activated`);
      await loadVendors();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not verify vendor");
    } finally {
      setBusy(false);
    }
  }

  async function toggleBlocked(vendor: Vendor) {
    setBusy(true);
    setError(null);
    try {
      if (vendor.status === "blocked") {
        await api.unblockVendor(token, vendor.id);
        setNotice(`${vendor.name} unblocked`);
      } else {
        await api.blockVendor(token, vendor.id);
        setNotice(`${vendor.name} blocked`);
      }
      await loadVendors();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not change vendor status");
    } finally {
      setBusy(false);
    }
  }

  const filterPills: { value: FilterValue; label: string }[] = [
    { value: "all", label: "All" },
    { value: "pending", label: "Pending Verification" },
    { value: "active", label: "Active" },
    { value: "blocked", label: "Blocked" },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-headline-md text-headline-md text-on-surface">Vendors</h2>
          <p className="text-xs text-on-surface-variant mt-0.5">
            Self-registered suppliers with admin verification status.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-error-container border border-error/20 px-4 py-3 text-sm text-on-error-container">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-lg bg-secondary-container/30 border border-secondary/20 px-4 py-3 text-sm text-on-secondary-container">
          {notice}
        </div>
      )}

      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card p-4">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
          <form
            className="relative w-full sm:max-w-xs"
            onSubmit={(event) => {
              event.preventDefault();
              loadVendors().catch((caught) =>
                setError(caught instanceof ApiError ? caught.message : "Search failed"),
              );
            }}
          >
            <Search className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={16} />
            <input
              className="field pl-9 pr-4"
              placeholder="Search by name, GST..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </form>

          <div className="flex items-center gap-2 flex-wrap">
            {filterPills.map((pill) => (
              <button
                key={pill.value}
                className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors border ${
                  statusFilter === pill.value
                    ? "bg-primary text-on-primary border-primary"
                    : "bg-transparent text-on-surface-variant border-outline-variant hover:bg-surface-container-high"
                }`}
                onClick={() => setStatusFilter(pill.value)}
              >
                {pill.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-left">
            <thead>
              <tr className="bg-surface-container-low border-b border-outline-variant">
                <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide">Vendor Name</th>
                <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide">Category</th>
                <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide">GST No</th>
                <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide">Contact</th>
                <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide">Stage</th>
                <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide">Status</th>
                {showActions && <th className="px-4 py-3 text-label-bold text-label-bold text-on-surface-variant font-semibold uppercase tracking-wide text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant text-body-dense">
              {vendors.map((vendor) => (
                <tr key={vendor.id} className="hover:bg-surface-container-low transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <VendorAvatar name={vendor.name} />
                      <div>
                        <p className="font-semibold text-on-surface">{vendor.name}</p>
                        <p className="text-xs text-on-surface-variant">
                          {vendor.city}, {vendor.state}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    {categoryById.get(vendor.category_id) ?? "-"}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-on-surface">{vendor.gstin}</td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    <p className="font-medium text-on-surface">{vendor.contact_name}</p>
                    <p className="text-xs">{vendor.contact_email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <StageBadge stage={vendor.lifecycle_stage} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={vendor.status} />
                  </td>
                  {showActions && (
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        {canVerify && vendor.status === "pending" && (
                          <button
                            className="btn-primary h-8 px-3 text-xs"
                            disabled={busy}
                            onClick={() => handleVerify(vendor)}
                            title="Verify and activate vendor"
                          >
                            Verify
                          </button>
                        )}
                        {canManageStatus && vendor.status !== "pending" && (
                          <button
                            className={
                              vendor.status === "blocked"
                                ? "btn-secondary h-8 w-8 px-0"
                                : "btn-danger h-8 w-8 px-0"
                            }
                            disabled={busy}
                            onClick={() => toggleBlocked(vendor)}
                            title={vendor.status === "blocked" ? "Unblock" : "Block"}
                          >
                            {vendor.status === "blocked" ? <RotateCcw size={14} /> : <Ban size={14} />}
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
              {vendors.length === 0 && (
                <tr>
                  <td
                    className="px-4 py-10 text-center text-on-surface-variant"
                    colSpan={showActions ? 7 : 6}
                  >
                    No vendors match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-outline-variant bg-surface-container-low">
          <p className="text-xs text-on-surface-variant">Showing {vendors.length} of {total} vendors</p>
        </div>
      </div>
    </div>
  );
}
