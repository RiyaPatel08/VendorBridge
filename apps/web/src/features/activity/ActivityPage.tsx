import { CheckCircle2, Hash, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { api, ApiError } from "../../lib/api";
import { shortHash } from "../../lib/format";
import type { ActivityLog, LedgerVerification } from "../../lib/types";

export function ActivityPage({ token }: { token: string }) {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [verification, setVerification] = useState<LedgerVerification | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadLogs() {
    const response = await api.activityLogs(token);
    setLogs(response);
  }

  useEffect(() => {
    loadLogs().catch((caught) =>
      setError(caught instanceof ApiError ? caught.message : "Could not load activity logs"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function verify() {
    setBusy(true);
    setError(null);
    try {
      const response = await api.verifyLedger(token);
      setVerification(response);
      await loadLogs();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not verify ledger");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="panel p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold">Activity Ledger</h2>
            <p className="mt-1 text-sm text-slate-600">{logs.length} recent entries</p>
          </div>
          <button className="btn-primary" onClick={verify} disabled={busy}>
            <ShieldCheck size={18} />
            Verify Integrity
          </button>
        </div>
        {verification && (
          <div
            className={`mt-4 flex items-start gap-3 rounded-md p-3 text-sm ${
              verification.ok ? "bg-teal-50 text-success" : "bg-red-50 text-danger"
            }`}
          >
            {verification.ok ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
            <div>
              <p className="font-semibold">{verification.message}</p>
              <p className="mt-1">
                Checked {verification.checked_entries} entries and {verification.checked_blocks} sealed blocks.
              </p>
            </div>
          </div>
        )}
      </section>

      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}

      <section className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] border-collapse text-left text-sm">
            <thead className="border-b border-line bg-field text-xs uppercase text-slate-600">
              <tr>
                <th className="px-4 py-3">Event</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Previous Hash</th>
                <th className="px-4 py-3">Entry Hash</th>
                <th className="px-4 py-3">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {logs.map((log) => (
                <tr key={log.id} className="bg-white">
                  <td className="px-4 py-3">
                    <p className="font-semibold">{log.summary}</p>
                    <p className="text-xs text-slate-500">{log.event_type}</p>
                  </td>
                  <td className="px-4 py-3">
                    {log.entity_type}
                    {log.entity_id ? ` #${log.entity_id}` : ""}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    <Hash className="mr-1 inline text-slate-400" size={14} />
                    {shortHash(log.previous_hash)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    <Hash className="mr-1 inline text-slate-400" size={14} />
                    {shortHash(log.entry_hash)}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{new Date(log.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td className="px-4 py-10 text-center text-slate-500" colSpan={5}>
                    No activity entries yet.
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

