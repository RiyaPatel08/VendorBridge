import { Ban, Edit3, Plus, RotateCcw, Save, Search, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ComplianceBadge, StageBadge, StatusBadge } from "../../components/Badge";
import { api, ApiError, type VendorPayload } from "../../lib/api";
import type { Vendor, VendorCategory, VendorStatus } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

const INDIA_STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
  "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
  "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
  "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
  "Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
  "Delhi","Jammu & Kashmir","Ladakh","Chandigarh","Puducherry",
];

const emptyForm: VendorPayload = {
  name: "",
  legal_name: "",
  category_id: 0,
  gstin: "",
  pan: "",
  state: "Gujarat",
  city: "",
  contact_name: "",
  contact_email: "",
  contact_phone: "",
  status: "pending",
  completed_orders_count: 0,
  rating: "0.00",
  reliability_score: "0.00",
  delivery_score: "0.00",
  completion_rate: "0.00",
  satisfaction_score: "0.00",
  compliance_notes: "",
};

const AVATAR_COLORS = [
  "bg-primary/20 text-primary",
  "bg-secondary/20 text-secondary",
  "bg-tertiary/20 text-tertiary",
  "bg-[#7c5071]/20 text-[#7c5071]",
  "bg-error/10 text-error",
];

function VendorAvatar({ name }: { name: string }) {
  const initials = name
    .split(" ")
    .slice(0, 2)
    .map((w) => w.charAt(0).toUpperCase())
    .join("");
  const color = AVATAR_COLORS[name.charCodeAt(0) % AVATAR_COLORS.length];
  return (
    <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold shrink-0 ${color}`}>
      {initials}
    </div>
  );
}

type FilterValue = "all" | VendorStatus;

export function VendorsPage({ token }: { token: string }) {
  const { user } = useAuth();
  // Admin: can verify (pending→active) and block/unblock. Cannot create or edit.
  const isAdminOnly = user?.role === "admin";
  // Officer: can create, edit, block/unblock. Cannot verify (admin-only action).
  const isOfficer = user?.role === "procurement_officer";
  // Either admin or officer can perform block/unblock actions
  const canManageStatus = isAdminOnly || isOfficer;
  // Either admin or officer see action column
  const showActions = isAdminOnly || isOfficer;

  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [categories, setCategories] = useState<VendorCategory[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<FilterValue>("all");
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Vendor | null>(null);
  const [form, setForm] = useState<VendorPayload>(emptyForm);

  const categoryById = useMemo(
    () => new Map(categories.map((c) => [c.id, c.name])),
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
      .then((items) => {
        setCategories(items);
        if (items.length > 0) {
          setForm((f) => ({ ...f, category_id: f.category_id || items[0].id }));
        }
      })
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load categories"));
  }, [token]);

  useEffect(() => {
    loadVendors().catch((caught) =>
      setError(caught instanceof ApiError ? caught.message : "Could not load vendors"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, statusFilter]);

  function resetForm() {
    setEditing(null);
    setForm({ ...emptyForm, category_id: categories[0]?.id ?? 0 });
    setShowForm(false);
  }

  function startEdit(vendor: Vendor) {
    setEditing(vendor);
    setForm({
      name: vendor.name,
      legal_name: vendor.legal_name ?? "",
      category_id: vendor.category_id,
      gstin: vendor.gstin,
      pan: vendor.pan ?? "",
      state: vendor.state,
      city: vendor.city,
      contact_name: vendor.contact_name,
      contact_email: vendor.contact_email,
      contact_phone: vendor.contact_phone,
      status: vendor.status,
      completed_orders_count: vendor.completed_orders_count,
      rating: vendor.rating,
      reliability_score: vendor.reliability_score,
      delivery_score: vendor.delivery_score,
      completion_rate: vendor.completion_rate,
      satisfaction_score: vendor.satisfaction_score,
      compliance_notes: vendor.compliance_notes ?? "",
    });
    setShowForm(true);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const payload = {
        ...form,
        gstin: form.gstin.toUpperCase(),
        pan: form.pan?.toUpperCase() || undefined,
        legal_name: form.legal_name || undefined,
        compliance_notes: form.compliance_notes || undefined,
      };
      if (editing) {
        await api.updateVendor(token, editing.id, payload);
        setNotice("Vendor updated successfully");
      } else {
        await api.createVendor(token, payload);
        setNotice("Vendor created successfully");
      }
      resetForm();
      await loadVendors();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not save vendor");
    } finally {
      setBusy(false);
    }
  }

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
    { value: "active", label: "Active" },
    { value: "blocked", label: "Blocked" },
    { value: "pending", label: "Pending" },
  ];

  return (
    <div className="space-y-5">
      {/* Header row */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-headline-md text-headline-md text-on-surface">Vendors</h2>
          {isAdminOnly && (
            <p className="text-xs text-on-surface-variant mt-0.5">
              Verify self-registered vendors to activate them on the platform
            </p>
          )}
        </div>
        {isOfficer && (
          <button
            className="btn-primary"
            onClick={() => {
              setShowForm(true);
              setEditing(null);
              setForm({ ...emptyForm, category_id: categories[0]?.id ?? 0 });
            }}
          >
            <Plus size={18} />
            Add Vendor
          </button>
        )}
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

      {/* Add/Edit form — officer only */}
      {showForm && isOfficer && (
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-title-sm text-title-sm text-on-surface">
              {editing ? "Edit Vendor" : "Add New Vendor"}
            </h3>
            <button className="btn-secondary h-8 w-8 px-0" onClick={resetForm}>
              <X size={16} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <label className="space-y-1 lg:col-span-2">
              <span className="label">Vendor name *</span>
              <input className="field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </label>
            <label className="space-y-1 lg:col-span-2">
              <span className="label">Legal name</span>
              <input className="field" value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} />
            </label>
            <label className="space-y-1">
              <span className="label">Category *</span>
              <select className="field" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: Number(e.target.value) })} required>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </label>
            <label className="space-y-1">
              <span className="label">Status</span>
              <select className="field" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as VendorStatus })}>
                <option value="pending">Pending</option>
                <option value="active">Active</option>
                <option value="blocked">Blocked</option>
              </select>
            </label>
            <label className="space-y-1">
              <span className="label">GSTIN *</span>
              <input className="field uppercase" minLength={15} maxLength={15} value={form.gstin} onChange={(e) => setForm({ ...form, gstin: e.target.value.toUpperCase() })} required />
            </label>
            <label className="space-y-1">
              <span className="label">PAN</span>
              <input className="field uppercase" minLength={10} maxLength={10} value={form.pan} onChange={(e) => setForm({ ...form, pan: e.target.value.toUpperCase() })} />
            </label>
            <label className="space-y-1">
              <span className="label">State *</span>
              <select className="field" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} required>
                {INDIA_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="space-y-1">
              <span className="label">City *</span>
              <input className="field" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} required />
            </label>
            <label className="space-y-1">
              <span className="label">Contact name *</span>
              <input className="field" value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} required />
            </label>
            <label className="space-y-1">
              <span className="label">Contact email *</span>
              <input className="field" type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} required />
            </label>
            <label className="space-y-1">
              <span className="label">Contact phone *</span>
              <input className="field" value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} required />
            </label>
            <label className="space-y-1">
              <span className="label">Completed orders</span>
              <input className="field" type="number" min={0} value={form.completed_orders_count} onChange={(e) => setForm({ ...form, completed_orders_count: Number(e.target.value) })} />
            </label>
            <label className="space-y-1">
              <span className="label">Rating (0–5)</span>
              <input className="field" type="number" min={0} max={5} step="0.01" value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} />
            </label>
            <label className="space-y-1">
              <span className="label">Reliability %</span>
              <input className="field" type="number" min={0} max={100} step="0.01" value={form.reliability_score} onChange={(e) => setForm({ ...form, reliability_score: e.target.value })} />
            </label>
            <label className="space-y-1">
              <span className="label">Delivery %</span>
              <input className="field" type="number" min={0} max={100} step="0.01" value={form.delivery_score} onChange={(e) => setForm({ ...form, delivery_score: e.target.value })} />
            </label>
            <label className="space-y-1">
              <span className="label">Completion %</span>
              <input className="field" type="number" min={0} max={100} step="0.01" value={form.completion_rate} onChange={(e) => setForm({ ...form, completion_rate: e.target.value })} />
            </label>
            <label className="space-y-1">
              <span className="label">Satisfaction %</span>
              <input className="field" type="number" min={0} max={100} step="0.01" value={form.satisfaction_score} onChange={(e) => setForm({ ...form, satisfaction_score: e.target.value })} />
            </label>
            <label className="space-y-1 lg:col-span-3">
              <span className="label">Compliance notes</span>
              <input className="field" value={form.compliance_notes} onChange={(e) => setForm({ ...form, compliance_notes: e.target.value })} />
            </label>
            <div className="flex items-end gap-2">
              <button className="btn-primary w-full" disabled={busy || !form.category_id}>
                <Save size={16} />
                {editing ? "Update" : "Create"}
              </button>
              <button type="button" className="btn-secondary h-10 w-10 px-0" onClick={resetForm}>
                <X size={16} />
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search + filters */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card p-4">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
          {/* Search */}
          <form
            className="relative w-full sm:max-w-xs"
            onSubmit={(e) => {
              e.preventDefault();
              loadVendors().catch((caught) =>
                setError(caught instanceof ApiError ? caught.message : "Search failed"),
              );
            }}
          >
            <Search className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={16} />
            <input
              className="field pl-9 pr-4"
              placeholder="Search by name, GST…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>

          {/* Filter pills */}
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

      {/* Vendors table */}
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
                    {categoryById.get(vendor.category_id) ?? "—"}
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
                        {/* Admin: verify pending vendors */}
                        {isAdminOnly && vendor.status === "pending" && (
                          <button
                            className="btn-primary h-8 px-3 text-xs"
                            disabled={busy}
                            onClick={() => handleVerify(vendor)}
                            title="Verify &amp; activate vendor"
                          >
                            Verify
                          </button>
                        )}
                        {/* Officer: edit vendor details */}
                        {isOfficer && (
                          <button
                            className="btn-secondary h-8 w-8 px-0"
                            onClick={() => startEdit(vendor)}
                            title="Edit vendor"
                          >
                            <Edit3 size={14} />
                          </button>
                        )}
                        {/* Both admin and officer can block/unblock */}
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
