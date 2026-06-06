import { CheckCircle2, ChevronDown, ChevronUp, Gauge, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { StageBadge } from "../../components/Badge";
import { api, ApiError } from "../../lib/api";
import { can } from "../../lib/permissions";
import type { ComparisonResponse, ComparisonRow, QuotationListItem, RFQ, RFQListItem } from "../../lib/types";
import { useAuth } from "../auth/AuthContext";

const SCORE_DIMENSIONS = [
  { key: "price_score", label: "Price", color: "#6d4262" },
  { key: "delivery_score", label: "Delivery", color: "#006a68" },
  { key: "vendor_rating_score", label: "Rating", color: "#005d1e" },
  { key: "compliance_score", label: "Compliance", color: "#875a7b" },
  { key: "payment_terms_score", label: "Payment", color: "#80747b" },
];

const RADAR_COLORS = ["#6d4262", "#006a68", "#005d1e", "#875a7b", "#ba1a1a"];

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-semibold text-on-surface-variant w-16 text-right truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-surface-container-high overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, value)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-bold text-on-surface w-8">{value.toFixed(0)}</span>
    </div>
  );
}

function ComparisonRadar({ rows }: { rows: ComparisonRow[] }) {
  const radarData = SCORE_DIMENSIONS.map((dim) => {
    const point: Record<string, unknown> = { dimension: dim.label };
    rows.forEach((row) => {
      point[row.vendor_name] = row.score_breakdown?.[dim.key] ?? 0;
    });
    return point;
  });

  return (
    <div className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
      <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
        <h3 className="font-title-sm text-title-sm text-on-surface">Best Value Score Comparison</h3>
        <p className="text-label-sm text-on-surface-variant mt-0.5">Multi-criteria vendor evaluation radar</p>
      </div>
      <div className="p-4 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData} outerRadius="75%">
            <PolarGrid stroke="#d2c2ca" />
            <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "#4e444a", fontWeight: 600 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: "#80747b" }} />
            {rows.map((row, i) => (
              <Radar
                key={row.quotation_id}
                name={row.vendor_name}
                dataKey={row.vendor_name}
                stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                fillOpacity={0.15}
                strokeWidth={2}
              />
            ))}
            <Legend
              verticalAlign="bottom"
              formatter={(value: string) => (
                <span className="text-xs font-semibold text-on-surface-variant">{value}</span>
              )}
            />
            <Tooltip
              contentStyle={{
                background: "#fff",
                border: "1px solid #d2c2ca",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

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
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
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
      {error && (
        <div className="rounded-lg bg-error-container border border-error/20 px-4 py-3 text-sm text-on-error-container">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-lg bg-secondary/10 border border-secondary/20 px-4 py-3 text-sm text-secondary font-semibold">
          {notice}
        </div>
      )}

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
        <>
          {/* Radar Chart */}
          {comparison?.rows && comparison.rows.length >= 2 && (
            <ComparisonRadar rows={comparison.rows} />
          )}

          <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
            <div className="border-b border-outline-variant p-4 bg-surface-bright">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-2">
                  <Gauge size={20} className="text-primary" />
                  <h2 className="font-title-sm text-title-sm text-on-surface">Quotation Comparison</h2>
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
                <thead className="border-b border-outline-variant bg-surface-container-low text-xs uppercase text-on-surface-variant">
                  <tr>
                    <th className="px-4 py-3 text-label-bold font-semibold">Vendor</th>
                    <th className="px-4 py-3 text-label-bold font-semibold">Grand Total</th>
                    <th className="px-4 py-3 text-label-bold font-semibold">Delivery</th>
                    <th className="px-4 py-3 text-label-bold font-semibold">Rating</th>
                    <th className="px-4 py-3 text-label-bold font-semibold">Lifecycle</th>
                    <th className="px-4 py-3 text-label-bold font-semibold">Coverage</th>
                    <th className="px-4 py-3 text-label-bold font-semibold">Best Value</th>
                    {canSelectQuote && <th className="px-4 py-3 text-label-bold font-semibold text-right">Action</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant">
                  {comparison?.rows.map((row) => (
                    <>
                      <tr
                        key={row.quotation_id}
                        className={`cursor-pointer transition-colors ${row.is_lowest_price ? "bg-secondary/5" : "bg-surface-container-lowest"} hover:bg-surface-container-low`}
                        onClick={() => setExpandedRow(expandedRow === row.quotation_id ? null : row.quotation_id)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-on-surface">{row.vendor_name}</span>
                            {row.is_lowest_price && (
                              <span className="bg-secondary/10 text-secondary text-[10px] font-bold px-1.5 py-0.5 rounded-full border border-secondary/20">
                                Lowest
                              </span>
                            )}
                            {expandedRow === row.quotation_id ? <ChevronUp size={14} className="text-on-surface-variant" /> : <ChevronDown size={14} className="text-on-surface-variant" />}
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-on-surface">₹{Number(row.grand_total).toLocaleString("en-IN")}</td>
                        <td className="px-4 py-3 text-on-surface">{row.delivery_days} days</td>
                        <td className="px-4 py-3 text-on-surface">{Number(row.vendor_rating).toFixed(1)} / 5</td>
                        <td className="px-4 py-3"><StageBadge stage={row.lifecycle_stage as never} /></td>
                        <td className="px-4 py-3 text-on-surface-variant text-xs">{row.coverage_label}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="h-2.5 w-24 rounded-full bg-surface-container-high overflow-hidden">
                              <div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${Math.min(100, Number(row.best_value_score))}%` }} />
                            </div>
                            <span className="font-bold text-on-surface text-sm">{Number(row.best_value_score).toFixed(1)}</span>
                          </div>
                        </td>
                        {canSelectQuote && (
                          <td className="px-4 py-3 text-right">
                            <button
                              className="btn-primary h-9"
                              disabled={busy}
                              onClick={(e) => { e.stopPropagation(); selectQuote(row.quotation_id); }}
                            >
                              <CheckCircle2 size={16} /> Select
                            </button>
                          </td>
                        )}
                      </tr>
                      {expandedRow === row.quotation_id && row.score_breakdown && (
                        <tr key={`${row.quotation_id}-breakdown`}>
                          <td colSpan={canSelectQuote ? 8 : 7} className="px-6 py-4 bg-surface-container-low border-t-0">
                            <p className="text-label-bold text-on-surface-variant uppercase tracking-wider mb-3">
                              Score Breakdown — {row.vendor_name}
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 max-w-2xl">
                              {SCORE_DIMENSIONS.map((dim) => (
                                <ScoreBar
                                  key={dim.key}
                                  label={dim.label}
                                  value={row.score_breakdown[dim.key] ?? 0}
                                  color={dim.color}
                                />
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                  {!comparison?.rows.length && (
                    <tr>
                      <td className="px-4 py-10 text-center text-on-surface-variant" colSpan={canSelectQuote ? 8 : 7}>
                        No submitted quotations yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl shadow-card overflow-hidden">
        <div className="px-5 py-4 border-b border-outline-variant bg-surface-bright">
          <h3 className="font-title-sm text-title-sm text-on-surface">All Quotations</h3>
        </div>
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-outline-variant bg-surface-container-low text-xs uppercase text-on-surface-variant">
            <tr>
              <th className="px-4 py-3 text-label-bold font-semibold">RFQ</th>
              {!isVendor && <th className="px-4 py-3 text-label-bold font-semibold">Vendor</th>}
              <th className="px-4 py-3 text-label-bold font-semibold">Total</th>
              <th className="px-4 py-3 text-label-bold font-semibold">Score</th>
              <th className="px-4 py-3 text-label-bold font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {quotations.map((quote) => (
              <tr key={quote.id} className="hover:bg-surface-container-low transition-colors">
                <td className="px-4 py-3 text-on-surface">{quote.rfq_title}</td>
                {!isVendor && <td className="px-4 py-3 text-on-surface font-medium">{quote.vendor_name}</td>}
                <td className="px-4 py-3 font-mono text-on-surface">₹{Number(quote.grand_total).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-16 rounded-full bg-surface-container-high overflow-hidden">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, Number(quote.best_value_score))}%` }} />
                    </div>
                    <span className="text-xs font-bold text-on-surface">{Number(quote.best_value_score).toFixed(1)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                    quote.status === "submitted" ? "bg-secondary/10 text-secondary border border-secondary/20" :
                    quote.status === "selected" ? "bg-tertiary/10 text-tertiary border border-tertiary/20" :
                    quote.status === "rejected" ? "bg-error-container text-on-error-container border border-error/20" :
                    "bg-surface-container text-on-surface-variant border border-outline-variant"
                  }`}>
                    {quote.status}
                  </span>
                </td>
              </tr>
            ))}
            {quotations.length === 0 && (
              <tr>
                <td className="px-4 py-10 text-center text-on-surface-variant" colSpan={isVendor ? 4 : 5}>
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
