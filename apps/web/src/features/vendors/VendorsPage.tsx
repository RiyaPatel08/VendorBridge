import { Ban, Edit3, Filter, Plus, RotateCcw, Save, Search, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ComplianceBadge, StageBadge, StatusBadge } from "../../components/Badge";
import { api, ApiError, type VendorPayload } from "../../lib/api";
import type { Vendor, VendorCategory, VendorStatus } from "../../lib/types";

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

export function VendorsPage({ token }: { token: string }) {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [categories, setCategories] = useState<VendorCategory[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | VendorStatus>("all");
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Vendor | null>(null);
  const [form, setForm] = useState<VendorPayload>(emptyForm);

  const categoryById = useMemo(
    () => new Map(categories.map((category) => [category.id, category.name])),
    [categories],
  );

  async function loadVendors() {
    const params = new URLSearchParams({ page: "1", page_size: "25" });
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
          setForm((current) => ({ ...current, category_id: current.category_id || items[0].id }));
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
        setNotice("Vendor updated");
      } else {
        await api.createVendor(token, payload);
        setNotice("Vendor created");
      }
      resetForm();
      await loadVendors();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not save vendor");
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

  return (
    <div className="space-y-5">
      <section className="panel p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Vendor Management</h2>
            <p className="mt-1 text-sm text-slate-600">{total} vendor records</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <form
              className="flex min-w-0 gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                loadVendors().catch((caught) =>
                  setError(caught instanceof ApiError ? caught.message : "Could not search vendors"),
                );
              }}
            >
              <div className="relative min-w-0 flex-1 sm:w-72">
                <Search className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={18} />
                <input
                  className="field pl-10"
                  placeholder="Search name, GSTIN, city"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <button className="btn-secondary" title="Search vendors">
                <Search size={18} />
              </button>
            </form>
            <div className="flex gap-2">
              <label className="relative">
                <Filter className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={18} />
                <select
                  className="field w-40 pl-10"
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as "all" | VendorStatus)}
                >
                  <option value="all">All</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="blocked">Blocked</option>
                </select>
              </label>
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
            </div>
          </div>
        </div>
      </section>

      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
      {notice && <div className="rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}

      {showForm && (
        <section className="panel p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h3 className="font-semibold">{editing ? "Edit Vendor" : "Add Vendor"}</h3>
            <button className="btn-secondary h-9 w-9 px-0" onClick={resetForm} title="Close form">
              <X size={18} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="grid gap-3 lg:grid-cols-4">
            <label className="space-y-1 lg:col-span-2">
              <span className="label">Vendor name</span>
              <input
                className="field"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                required
              />
            </label>
            <label className="space-y-1 lg:col-span-2">
              <span className="label">Legal name</span>
              <input
                className="field"
                value={form.legal_name}
                onChange={(event) => setForm({ ...form, legal_name: event.target.value })}
              />
            </label>
            <label className="space-y-1">
              <span className="label">Category</span>
              <select
                className="field"
                value={form.category_id}
                onChange={(event) => setForm({ ...form, category_id: Number(event.target.value) })}
                required
              >
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1">
              <span className="label">Status</span>
              <select
                className="field"
                value={form.status}
                onChange={(event) => setForm({ ...form, status: event.target.value as VendorStatus })}
              >
                <option value="pending">Pending</option>
                <option value="active">Active</option>
                <option value="blocked">Blocked</option>
              </select>
            </label>
            <label className="space-y-1">
              <span className="label">GSTIN</span>
              <input
                className="field uppercase"
                minLength={15}
                maxLength={15}
                value={form.gstin}
                onChange={(event) => setForm({ ...form, gstin: event.target.value.toUpperCase() })}
                required
              />
            </label>
            <label className="space-y-1">
              <span className="label">PAN</span>
              <input
                className="field uppercase"
                minLength={10}
                maxLength={10}
                value={form.pan}
                onChange={(event) => setForm({ ...form, pan: event.target.value.toUpperCase() })}
              />
            </label>
            <label className="space-y-1">
              <span className="label">State</span>
              <input
                className="field"
                value={form.state}
                onChange={(event) => setForm({ ...form, state: event.target.value })}
                required
              />
            </label>
            <label className="space-y-1">
              <span className="label">City</span>
              <input
                className="field"
                value={form.city}
                onChange={(event) => setForm({ ...form, city: event.target.value })}
                required
              />
            </label>
            <label className="space-y-1">
              <span className="label">Contact</span>
              <input
                className="field"
                value={form.contact_name}
                onChange={(event) => setForm({ ...form, contact_name: event.target.value })}
                required
              />
            </label>
            <label className="space-y-1">
              <span className="label">Email</span>
              <input
                className="field"
                type="email"
                value={form.contact_email}
                onChange={(event) => setForm({ ...form, contact_email: event.target.value })}
                required
              />
            </label>
            <label className="space-y-1">
              <span className="label">Phone</span>
              <input
                className="field"
                value={form.contact_phone}
                onChange={(event) => setForm({ ...form, contact_phone: event.target.value })}
                required
              />
            </label>
            <label className="space-y-1">
              <span className="label">Completed orders</span>
              <input
                className="field"
                type="number"
                min={0}
                value={form.completed_orders_count}
                onChange={(event) =>
                  setForm({ ...form, completed_orders_count: Number(event.target.value) })
                }
              />
            </label>
            <label className="space-y-1">
              <span className="label">Rating</span>
              <input
                className="field"
                type="number"
                min={0}
                max={5}
                step="0.01"
                value={form.rating}
                onChange={(event) => setForm({ ...form, rating: event.target.value })}
              />
            </label>
            <label className="space-y-1">
              <span className="label">Reliability</span>
              <input
                className="field"
                type="number"
                min={0}
                max={100}
                step="0.01"
                value={form.reliability_score}
                onChange={(event) => setForm({ ...form, reliability_score: event.target.value })}
              />
            </label>
            <label className="space-y-1">
              <span className="label">Delivery</span>
              <input
                className="field"
                type="number"
                min={0}
                max={100}
                step="0.01"
                value={form.delivery_score}
                onChange={(event) => setForm({ ...form, delivery_score: event.target.value })}
              />
            </label>
            <label className="space-y-1">
              <span className="label">Completion</span>
              <input
                className="field"
                type="number"
                min={0}
                max={100}
                step="0.01"
                value={form.completion_rate}
                onChange={(event) => setForm({ ...form, completion_rate: event.target.value })}
              />
            </label>
            <label className="space-y-1">
              <span className="label">Satisfaction</span>
              <input
                className="field"
                type="number"
                min={0}
                max={100}
                step="0.01"
                value={form.satisfaction_score}
                onChange={(event) => setForm({ ...form, satisfaction_score: event.target.value })}
              />
            </label>
            <label className="space-y-1 lg:col-span-3">
              <span className="label">Compliance notes</span>
              <input
                className="field"
                value={form.compliance_notes}
                onChange={(event) => setForm({ ...form, compliance_notes: event.target.value })}
              />
            </label>
            <div className="flex items-end gap-2">
              <button className="btn-primary w-full" disabled={busy || !form.category_id}>
                <Save size={18} />
                {editing ? "Save" : "Create"}
              </button>
              <button type="button" className="btn-secondary" onClick={resetForm}>
                <X size={18} />
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[960px] border-collapse text-left text-sm">
            <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
              <tr>
                <th className="px-4 py-3">Vendor</th>
                <th className="px-4 py-3">GSTIN</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Lifecycle</th>
                <th className="px-4 py-3">Compliance</th>
                <th className="px-4 py-3">Rating</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {vendors.map((vendor) => (
                <tr key={vendor.id} className="bg-white hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="font-semibold">{vendor.name}</p>
                    <p className="text-xs text-slate-500">
                      {vendor.city}, {vendor.state} · {vendor.contact_email}
                    </p>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{vendor.gstin}</td>
                  <td className="px-4 py-3">{categoryById.get(vendor.category_id) ?? "Unassigned"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={vendor.status} />
                  </td>
                  <td className="px-4 py-3">
                    <StageBadge stage={vendor.lifecycle_stage} />
                  </td>
                  <td className="px-4 py-3">
                    <ComplianceBadge value={vendor.compliance_badge} />
                  </td>
                  <td className="px-4 py-3">{Number(vendor.rating).toFixed(2)} / 5</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <button className="btn-secondary h-9 w-9 px-0" onClick={() => startEdit(vendor)} title="Edit vendor">
                        <Edit3 size={16} />
                      </button>
                      <button
                        className={vendor.status === "blocked" ? "btn-secondary h-9 w-9 px-0" : "btn-danger h-9 w-9 px-0"}
                        disabled={busy}
                        onClick={() => toggleBlocked(vendor)}
                        title={vendor.status === "blocked" ? "Unblock vendor" : "Block vendor"}
                      >
                        {vendor.status === "blocked" ? <RotateCcw size={16} /> : <Ban size={16} />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {vendors.length === 0 && (
                <tr>
                  <td className="px-4 py-10 text-center text-slate-500" colSpan={8}>
                    No vendors match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
