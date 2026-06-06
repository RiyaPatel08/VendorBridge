import { Download, Mail, Printer, ReceiptIndianRupee } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../../lib/api";
import { can } from "../../lib/permissions";
import type { InvoiceListItem, PurchaseOrderListItem } from "../../lib/types";

export function InvoicesPage({ token }: { token: string }) {
  const { user } = useAuth();
  const canGenerateInvoice = can(user?.role, "generateInvoice");
  const canMarkPayable = can(user?.role, "markInvoicePayable");
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [orders, setOrders] = useState<PurchaseOrderListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    const [invoiceRows, poRows] = await Promise.all([api.invoices(token), api.purchaseOrders(token)]);
    setInvoices(invoiceRows);
    setOrders(poRows);
  }

  useEffect(() => {
    load().catch((caught) => setError(caught instanceof ApiError ? caught.message : "Could not load invoices"));
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

  async function downloadInvoice(id: number) {
    const response = await fetch(`http://localhost:8000/api/v1/invoices/${id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `invoice-${id}.html`;
    link.click();
    URL.revokeObjectURL(url);
    await load();
  }

  return (
    <div className="space-y-4">
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
      {notice && <div className="rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}
      {canGenerateInvoice && orders.length > 0 && (
        <section className="panel p-4">
          <div className="flex flex-wrap gap-2">
            {orders.map((po) => (
              <button key={po.id} className="btn-secondary" disabled={busy} onClick={() => act("Invoice generated", () => api.generateInvoice(token, po.id))}>
                <ReceiptIndianRupee size={18} /> Generate for {po.po_number}
              </button>
            ))}
          </div>
        </section>
      )}
      <section className="panel overflow-hidden">
        <table className="w-full min-w-[940px] text-left text-sm">
          <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
            <tr><th className="px-4 py-3">Invoice</th><th className="px-4 py-3">PO</th><th className="px-4 py-3">Vendor</th><th className="px-4 py-3">Total</th><th className="px-4 py-3">3-way Match</th><th className="px-4 py-3">Status</th><th className="px-4 py-3 text-right">Actions</th></tr>
          </thead>
          <tbody className="divide-y divide-line">
            {invoices.map((invoice) => (
              <tr key={invoice.id}>
                <td className="px-4 py-3 font-semibold">{invoice.invoice_number}</td>
                <td className="px-4 py-3">{invoice.po_number}</td>
                <td className="px-4 py-3">{invoice.vendor_name}</td>
                <td className="px-4 py-3">INR {Number(invoice.grand_total).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3">{invoice.match_status}</td>
                <td className="px-4 py-3">{invoice.status}</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    <button className="btn-secondary h-9 w-9 px-0" title="Print" onClick={() => act("Print logged", () => api.printInvoice(token, invoice.id))}><Printer size={16} /></button>
                    <button className="btn-secondary h-9 w-9 px-0" title="Download" onClick={() => act("Download logged", () => downloadInvoice(invoice.id))}><Download size={16} /></button>
                    <button className="btn-secondary h-9 w-9 px-0" title="Email" onClick={() => act("Email queued", () => api.emailInvoice(token, invoice.id, "accounts@infrasupplies.com"))}><Mail size={16} /></button>
                    {canMarkPayable && (
                      <button className="btn-primary h-9" disabled={busy || invoice.status === "payable"} onClick={() => act("Marked payable", () => api.markPayable(token, invoice.id))}>Payable</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {!invoices.length && <tr><td colSpan={7} className="px-4 py-10 text-center text-slate-500">No invoices yet.</td></tr>}
          </tbody>
        </table>
      </section>
    </div>
  );
}
