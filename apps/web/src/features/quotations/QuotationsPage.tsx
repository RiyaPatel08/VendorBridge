import { CheckCircle2, Gauge, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { StageBadge } from "../../components/Badge";
import { api, ApiError } from "../../lib/api";
import { can } from "../../lib/permissions";
import type { ComparisonResponse, QuotationListItem, RFQ, RFQListItem } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

export function QuotationsPage({ token }: { token: string }) {
  const { user } = useAuth();
  const role = user?.role;
  const isVendor = role === "vendor";
  const canCompare = can(role, "compareQuotations");
  const canSelectQuote = can(role, "selectQuotation");
  const [rfqs, setRfqs] = useState<RFQListItem[]>([]);
  const [rfqDetail, setRfqDetail] = useState<RFQ | null>(null);
  const [quotations, setQuotations] = useState<QuotationListItem[]>([]);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [selectedRfqId, setSelectedRfqId] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    const [rfqRows, quotationRows] = await Promise.all([api.rfqs(token), api.quotations(token)]);
    setRfqs(rfqRows);
    setQuotations(quotationRows);
    const firstSent = rfqRows.find((rfq) => rfq.status === "sent") ?? rfqRows[0];
    if (firstSent && !selectedRfqId) {
      setSelectedRfqId(firstSent.id);
    }
  }

  async function loadDetail(id: number) {
    const detail = await api.rfq(token, id);
    setRfqDetail(detail);
    if (canCompare) {
      setComparison(await api.comparison(token, id).catch(() => null));
    } else {
      setComparison(null);
    }
  }

  useEffect(() => {
    load().catch((caught) =>
      setError(caught instanceof ApiError ? caught.message : "Could not load quotations"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (selectedRfqId) {
      loadDetail(selectedRfqId).catch((caught) =>
        setError(caught instanceof ApiError ? caught.message : "Could not load RFQ detail"),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRfqId, canCompare]);

  async function submitQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!rfqDetail) return;
    const vendorId = rfqDetail.invites[0]?.vendor_id;
    if (!vendorId) {
      setError("Your verified vendor profile is not invited to this RFQ.");
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const payload = {
        rfq_id: rfqDetail.id,
        vendor_id: vendorId,
        delivery_days: 10,
        payment_terms_days: 30,
        notes: "Submitted from VendorBridge supplier portal.",
        items: rfqDetail.items.map((item, index) => ({
          rfq_item_id: item.id,
          quantity: item.quantity,
          unit_price: index === 0 ? "4200.00" : "5200.00",
          gst_percent: "18.00",
          available_quantity: item.quantity,
          additional_quantity: "0.00",
          additional_available_days: null,
        })),
      };
      const draft = await api.saveQuotation(token, payload);
      await api.submitQuotation(token, draft.id);
      setNotice("Quotation submitted");
      await load();
      await loadDetail(rfqDetail.id);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not submit quotation");
    } finally {
      setBusy(false);
    }
  }

  async function selectQuote(quotationId: number) {
    if (!selectedRfqId) return;
    setBusy(true);
    setError(null);
    try {
      const response = await api.selectQuotation(token, selectedRfqId, quotationId);
      setNotice(`Approval #${response.approval_request_id} created`);
      await loadDetail(selectedRfqId);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not select quotation");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
      {notice && <div className="rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}

      {isVendor && (
        <section className="panel p-4">
          <form onSubmit={submitQuote} className="grid gap-3 md:grid-cols-[1fr_auto]">
            <label className="space-y-1">
              <span className="label">RFQ received</span>
              <select
                className="field"
                value={selectedRfqId}
                onChange={(event) => setSelectedRfqId(Number(event.target.value))}
              >
                <option value={0}>Select RFQ</option>
                {rfqs.map((rfq) => (
                  <option key={rfq.id} value={rfq.id}>{rfq.title}</option>
                ))}
              </select>
            </label>
            <button className="btn-primary self-end" disabled={busy || !rfqDetail}>
              <Send size={18} /> Submit Quotation
            </button>
          </form>
        </section>
      )}

      {canCompare && (
        <section className="panel overflow-hidden">
          <div className="border-b border-line p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-2">
                <Gauge size={20} className="text-brand" />
                <h2 className="font-semibold">Quotation Comparison</h2>
              </div>
              <select
                className="field md:max-w-sm"
                value={selectedRfqId}
                onChange={(event) => setSelectedRfqId(Number(event.target.value))}
              >
                <option value={0}>Select RFQ</option>
                {rfqs.map((rfq) => (
                  <option key={rfq.id} value={rfq.id}>{rfq.title}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
                <tr>
                  <th className="px-4 py-3">Vendor</th>
                  <th className="px-4 py-3">Grand Total</th>
                  <th className="px-4 py-3">Delivery</th>
                  <th className="px-4 py-3">Rating</th>
                  <th className="px-4 py-3">Lifecycle</th>
                  <th className="px-4 py-3">Coverage</th>
                  <th className="px-4 py-3">Best Value</th>
                  {canSelectQuote && <th className="px-4 py-3 text-right">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {comparison?.rows.map((row) => (
                  <tr key={row.quotation_id} className={row.is_lowest_price ? "bg-teal-50" : "bg-white"}>
                    <td className="px-4 py-3 font-semibold">
                      {row.vendor_name}
                      {row.is_lowest_price && <span className="ml-2 text-xs text-success">Lowest</span>}
                    </td>
                    <td className="px-4 py-3">INR {Number(row.grand_total).toLocaleString("en-IN")}</td>
                    <td className="px-4 py-3">{row.delivery_days} days</td>
                    <td className="px-4 py-3">{Number(row.vendor_rating).toFixed(1)} / 5</td>
                    <td className="px-4 py-3"><StageBadge stage={row.lifecycle_stage as never} /></td>
                    <td className="px-4 py-3">{row.coverage_label}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-24 rounded-full bg-slate-100">
                          <div className="h-2 rounded-full bg-brand" style={{ width: `${Math.min(100, Number(row.best_value_score))}%` }} />
                        </div>
                        <span className="font-semibold">{Number(row.best_value_score).toFixed(2)}</span>
                      </div>
                    </td>
                    {canSelectQuote && (
                      <td className="px-4 py-3 text-right">
                        <button className="btn-primary h-9" disabled={busy} onClick={() => selectQuote(row.quotation_id)}>
                          <CheckCircle2 size={16} /> Send for Approval
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {!comparison?.rows.length && (
                  <tr>
                    <td className="px-4 py-10 text-center text-slate-500" colSpan={canSelectQuote ? 8 : 7}>
                      No submitted quotations yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="panel overflow-hidden">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
            <tr>
              <th className="px-4 py-3">RFQ</th>
              {!isVendor && <th className="px-4 py-3">Vendor</th>}
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {quotations.map((quote) => (
              <tr key={quote.id}>
                <td className="px-4 py-3">{quote.rfq_title}</td>
                {!isVendor && <td className="px-4 py-3">{quote.vendor_name}</td>}
                <td className="px-4 py-3">INR {Number(quote.grand_total).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3">{Number(quote.best_value_score).toFixed(2)}</td>
                <td className="px-4 py-3">{quote.status}</td>
              </tr>
            ))}
            {quotations.length === 0 && (
              <tr>
                <td className="px-4 py-10 text-center text-slate-500" colSpan={isVendor ? 4 : 5}>
                  No quotations available for your role yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
