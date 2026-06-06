import { CheckCircle2, MessageCircleWarning, PackageCheck, Truck, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../../lib/api";
import { can } from "../../lib/permissions";
import type { PurchaseOrderListItem } from "../../lib/types";

const nextDelivery: Record<string, string> = {
  not_started: "packed",
  packed: "shipped",
  shipped: "in_transit",
  in_transit: "delivered",
};

export function PurchaseOrdersPage({ token }: { token: string }) {
  const { user } = useAuth();
  const canAcceptReject = can(user?.role, "acceptPurchaseOrder");
  const canUpdateDelivery = can(user?.role, "updateDelivery");
  const canReceive = can(user?.role, "receivePurchaseOrder");
  const [orders, setOrders] = useState<PurchaseOrderListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setOrders(await api.purchaseOrders(token));
  }

  useEffect(() => {
    load().catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load POs"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function act(label: string, fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      setNotice(label);
      await load();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
      {notice && <div className="rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}
      <section className="panel overflow-hidden">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
            <tr><th className="px-4 py-3">PO</th><th className="px-4 py-3">Vendor</th><th className="px-4 py-3">Total</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Delivery</th><th className="px-4 py-3 text-right">Actions</th></tr>
          </thead>
          <tbody className="divide-y divide-line">
            {orders.map((po) => (
              <tr key={po.id}>
                <td className="px-4 py-3 font-semibold">{po.po_number}</td>
                <td className="px-4 py-3">{po.vendor_name}</td>
                <td className="px-4 py-3">INR {Number(po.grand_total).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3">{po.status} | {po.acceptance_status}</td>
                <td className="px-4 py-3">{po.delivery_status}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    {canAcceptReject && (
                      <>
                        <button className="btn-secondary h-9" disabled={busy || po.acceptance_status === "accepted"} onClick={() => act("PO accepted", () => api.acceptPo(token, po.id))}><CheckCircle2 size={16} /> Accept</button>
                        <button className="btn-secondary h-9" disabled={busy || po.acceptance_status === "rejected"} onClick={() => act("PO rejected", () => api.rejectPo(token, po.id))}><XCircle size={16} /> Reject</button>
                        <button className="btn-secondary h-9" disabled={busy || po.acceptance_status === "modification_requested"} onClick={() => act("Modification requested", () => api.requestPoModification(token, po.id))}><MessageCircleWarning size={16} /> Changes</button>
                      </>
                    )}
                    {canUpdateDelivery && (
                      <button className="btn-secondary h-9" disabled={busy || po.delivery_status === "delivered"} onClick={() => act("Delivery updated", () => api.updateDelivery(token, po.id, nextDelivery[po.delivery_status] ?? "delivered"))}><Truck size={16} /> Move</button>
                    )}
                    {canReceive && (
                      <button className="btn-primary h-9" disabled={busy || po.status === "received"} onClick={() => act("Receipt confirmed", () => api.receivePo(token, po.id))}><PackageCheck size={16} /> Receive</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {!orders.length && <tr><td colSpan={6} className="px-4 py-10 text-center text-slate-500">No purchase orders yet.</td></tr>}
          </tbody>
        </table>
      </section>
    </div>
  );
}
