import { Send, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { StatusBadge } from "../../components/Badge";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError, type RFQPayload } from "../../lib/api";
import type { RFQListItem, Vendor, VendorCategory } from "../../lib/types";

export function RfqsPage({ token }: { token: string }) {
  const { user } = useAuth();
  const isOfficer = user?.role === "procurement_officer";
  const [rfqs, setRfqs] = useState<RFQListItem[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [categories, setCategories] = useState<VendorCategory[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const defaultDeadline = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() + 14);
    return date.toISOString().slice(0, 16);
  }, []);
  const [form, setForm] = useState({
    title: "Office Furniture Procurement Q2",
    category_id: 0,
    description: "Ergonomic chairs and standing desks for the Q2 office expansion.",
    deadline: defaultDeadline,
    vendor_ids: [] as number[],
  });

  async function load() {
    const [rfqRows, categoryRows, vendorRows] = await Promise.all([
      api.rfqs(token),
      api.categories(token),
      api.vendors(token, new URLSearchParams({ page: "1", page_size: "50", status: "active" })),
    ]);
    setRfqs(rfqRows);
    setCategories(categoryRows);
    setVendors(vendorRows.items);
    setForm((current) => ({
      ...current,
      category_id: current.category_id || categoryRows[0]?.id || 0,
      vendor_ids: current.vendor_ids.length ? current.vendor_ids : vendorRows.items.slice(0, 3).map((v) => v.id),
    }));
  }

  useEffect(() => {
    load().catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load RFQs"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function createRfq(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const payload: RFQPayload = {
        ...form,
        deadline: new Date(form.deadline).toISOString(),
        items: [
          { item_name: "Ergonomic chair", hsn_sac: "9403", quantity: "25", unit: "NOS", target_price: "5000" },
          { item_name: "Standing desk", hsn_sac: "9403", quantity: "10", unit: "NOS", target_price: "9000" },
        ],
      };
      const rfq = await api.createRfq(token, payload);
      setNotice(`Created RFQ #${rfq.id}`);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not create RFQ");
    } finally {
      setBusy(false);
    }
  }

  async function send(id: number) {
    setBusy(true);
    setError(null);
    try {
      await api.sendRfq(token, id);
      setNotice("RFQ sent to vendors");
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not send RFQ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      {isOfficer && (
        <section className="panel p-4">
          <div className="mb-4 flex items-center gap-2">
            <Sparkles size={20} className="text-brand" />
            <h2 className="text-lg font-semibold">Create RFQ</h2>
          </div>
          {error && <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
          {notice && <div className="mb-3 rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}
          <form onSubmit={createRfq} className="grid gap-3 lg:grid-cols-4">
            <label className="space-y-1 lg:col-span-2">
              <span className="label">Title</span>
              <input className="field" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
            </label>
            <label className="space-y-1">
              <span className="label">Category</span>
              <select className="field" value={form.category_id} onChange={(event) => setForm({ ...form, category_id: Number(event.target.value) })}>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </select>
            </label>
            <label className="space-y-1">
              <span className="label">Deadline</span>
              <input className="field" type="datetime-local" value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} />
            </label>
            <label className="space-y-1 lg:col-span-4">
              <span className="label">Description</span>
              <input className="field" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
            </label>
            <div className="lg:col-span-4">
              <p className="label mb-2">Assigned vendors</p>
              <div className="grid gap-2 md:grid-cols-3">
                {vendors.map((vendor) => (
                  <label key={vendor.id} className="flex items-center gap-2 rounded-md border border-line bg-white p-2 text-sm">
                    <input
                      type="checkbox"
                      checked={form.vendor_ids.includes(vendor.id)}
                      onChange={(event) => {
                        const vendor_ids = event.target.checked
                          ? [...form.vendor_ids, vendor.id]
                          : form.vendor_ids.filter((id) => id !== vendor.id);
                        setForm({ ...form, vendor_ids });
                      }}
                    />
                    {vendor.name}
                  </label>
                ))}
              </div>
            </div>
            <button className="btn-primary lg:col-span-1" disabled={busy || !form.category_id || form.vendor_ids.length === 0}>
              Create RFQ
            </button>
          </form>
        </section>
      )}

      {!isOfficer && (error || notice) && (
        <div>
          {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
          {notice && <div className="rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}
        </div>
      )}

      <section className="panel overflow-hidden">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
            <tr>
              <th className="px-4 py-3">RFQ</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Deadline</th>
              <th className="px-4 py-3">Quotes</th>
              <th className="px-4 py-3">Status</th>
              {isOfficer && <th className="px-4 py-3 text-right">Action</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rfqs.map((rfq) => (
              <tr key={rfq.id}>
                <td className="px-4 py-3 font-semibold">{rfq.title}</td>
                <td className="px-4 py-3">{rfq.category_name}</td>
                <td className="px-4 py-3">{new Date(rfq.deadline).toLocaleDateString()}</td>
                <td className="px-4 py-3">{rfq.quote_count} / {rfq.invite_count}</td>
                <td className="px-4 py-3"><StatusBadge status={rfq.status === "draft" ? "pending" : "active"} /></td>
                {isOfficer && (
                  <td className="px-4 py-3 text-right">
                    {rfq.status === "draft" && (
                      <button className="btn-primary h-9" disabled={busy} onClick={() => send(rfq.id)}>
                        <Send size={16} /> Send
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

