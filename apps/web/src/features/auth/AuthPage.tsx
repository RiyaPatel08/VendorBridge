import { KeyRound, Lock, Mail, UserPlus } from "lucide-react";
import { FormEvent, useState } from "react";
import { api, ApiError } from "../../lib/api";
import type { UserRole } from "../../lib/types";
import { roleLabel } from "../../lib/format";
import { useAuth } from "./AuthContext";

type Mode = "login" | "register" | "forgot";

const roleOptions: UserRole[] = ["procurement_officer", "manager", "vendor"];

export function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "officer@vendorbridge.test",
    phone: "+91 90000 00000",
    role: "procurement_officer" as UserRole,
    password: "VendorBridge@123",
  });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      if (mode === "login") {
        await login(form.email, form.password);
      } else if (mode === "register") {
        await register(form);
      } else {
        const response = await api.forgotPassword(form.email);
        setNotice(response.message);
      }
    } catch (caught) {
      const message = caught instanceof ApiError ? caught.message : "Something went wrong";
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <div className="mx-auto grid min-h-screen w-full max-w-6xl grid-cols-1 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="flex flex-col justify-between bg-ink px-6 py-8 text-white sm:px-10">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-cyan-600 font-bold">
                VB
              </div>
              <div>
                <p className="text-lg font-semibold">VendorBridge</p>
                <p className="text-sm text-slate-300">Procurement ERP Console</p>
              </div>
            </div>
            <div className="mt-12 max-w-xl">
              <h1 className="text-3xl font-semibold leading-tight sm:text-4xl">
                Procurement workspace
              </h1>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                Sign in to manage vendors, approvals, documents, and activity records.
              </p>
            </div>
          </div>
          <div className="mt-10 text-sm text-slate-300">BuzzBeatStrong · Odoo Hackathon</div>
        </section>

        <section className="flex items-center justify-center px-4 py-8 sm:px-8">
          <form onSubmit={handleSubmit} className="panel w-full max-w-md p-6">
            <div className="mb-6 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-ink">
                  {mode === "login" ? "Sign in" : mode === "register" ? "Create account" : "Reset access"}
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  {mode === "login"
                    ? "Use a demo credential or your registered account."
                    : mode === "register"
                      ? "Register a role-scoped user for local testing."
                      : "A reset request is logged without sending external email."}
                </p>
              </div>
              {mode === "login" ? <KeyRound size={24} /> : <UserPlus size={24} />}
            </div>

            {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-danger">{error}</div>}
            {notice && <div className="mb-4 rounded-md bg-teal-50 p-3 text-sm text-success">{notice}</div>}

            {mode === "register" && (
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="space-y-1">
                  <span className="label">First name</span>
                  <input
                    className="field"
                    value={form.first_name}
                    onChange={(event) => setForm({ ...form, first_name: event.target.value })}
                    required
                  />
                </label>
                <label className="space-y-1">
                  <span className="label">Last name</span>
                  <input
                    className="field"
                    value={form.last_name}
                    onChange={(event) => setForm({ ...form, last_name: event.target.value })}
                    required
                  />
                </label>
                <label className="space-y-1 sm:col-span-2">
                  <span className="label">Phone</span>
                  <input
                    className="field"
                    value={form.phone}
                    onChange={(event) => setForm({ ...form, phone: event.target.value })}
                  />
                </label>
                <label className="space-y-1 sm:col-span-2">
                  <span className="label">Role</span>
                  <select
                    className="field"
                    value={form.role}
                    onChange={(event) => setForm({ ...form, role: event.target.value as UserRole })}
                  >
                    {roleOptions.map((role) => (
                      <option key={role} value={role}>
                        {roleLabel(role)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            )}

            <div className="mt-3 space-y-3">
              <label className="space-y-1">
                <span className="label">Email</span>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={18} />
                  <input
                    className="field pl-10"
                    type="email"
                    value={form.email}
                    onChange={(event) => setForm({ ...form, email: event.target.value })}
                    required
                  />
                </div>
              </label>
              {mode !== "forgot" && (
                <label className="space-y-1">
                  <span className="label">Password</span>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3 top-2.5 text-slate-400" size={18} />
                    <input
                      className="field pl-10"
                      type="password"
                      minLength={8}
                      value={form.password}
                      onChange={(event) => setForm({ ...form, password: event.target.value })}
                      required
                    />
                  </div>
                </label>
              )}
            </div>

            <button className="btn-primary mt-5 w-full" disabled={busy}>
              {busy ? "Working..." : mode === "login" ? "Sign in" : mode === "register" ? "Create account" : "Request reset"}
            </button>

            <div className="mt-5 flex flex-wrap items-center justify-between gap-2 text-sm">
              <button type="button" className="font-semibold text-brand" onClick={() => setMode("login")}>
                Sign in
              </button>
              <button type="button" className="font-semibold text-brand" onClick={() => setMode("register")}>
                Register
              </button>
              <button type="button" className="font-semibold text-brand" onClick={() => setMode("forgot")}>
                Forgot password
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
