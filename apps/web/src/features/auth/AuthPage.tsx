import { Eye, EyeOff, Lock, Mail, User } from "lucide-react";
import { FormEvent, useState } from "react";
import { api, ApiError, type VendorRegistrationFields } from "../../lib/api";
import type { UserRole } from "../../lib/types";
import { useAuth } from "./AuthContext";

type Mode = "login" | "register" | "forgot";

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "procurement_officer", label: "Procurement Officer" },
  { value: "manager", label: "Manager / Approver" },
  { value: "finance_manager", label: "Finance Manager" },
  { value: "vendor", label: "Vendor" },
];

const INDIA_STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
  "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
  "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
  "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
  "Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
  "Delhi","Jammu & Kashmir","Ladakh","Chandigarh","Puducherry",
];

const PRODUCT_CATEGORIES = [
  "Furniture","Office Supplies","IT Equipment","Logistics",
  "Manufacturing","Construction","Healthcare","Automotive",
  "Textile","Food & Beverage","Electronics","Chemicals",
];

export function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Login form
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });

  // Registration form
  const [regForm, setRegForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    role: "procurement_officer" as UserRole,
    password: "",
    confirm_password: "",
    // Vendor-specific fields
    company_name: "",
    gstin: "",
    pan: "",
    state: "Gujarat",
    city: "",
    category_name: "IT Equipment",
    bank_account_name: "",
    bank_account_number: "",
    ifsc_code: "",
  });

  const [forgotEmail, setForgotEmail] = useState("");

  const isVendor = regForm.role === "vendor";

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(loginForm.email, loginForm.password);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Invalid email or password");
    } finally {
      setBusy(false);
    }
  }

  async function handleRegister(event: FormEvent) {
    event.preventDefault();
    if (regForm.password !== regForm.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    if (isVendor && !regForm.gstin) {
      setError("GST Number is required for vendor registration");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const vendorFields: VendorRegistrationFields | undefined = isVendor
        ? {
            company_name: regForm.company_name,
            gstin: regForm.gstin.toUpperCase(),
            pan: regForm.pan.toUpperCase() || undefined,
            state: regForm.state,
            city: regForm.city,
            category_name: regForm.category_name,
            bank_details: [
              regForm.bank_account_name && `Account: ${regForm.bank_account_name}`,
              regForm.bank_account_number && `Number: ${regForm.bank_account_number}`,
              regForm.ifsc_code && `IFSC: ${regForm.ifsc_code}`,
            ]
              .filter(Boolean)
              .join(", ") || undefined,
          }
        : undefined;

      await register(
        {
          first_name: regForm.first_name,
          last_name: regForm.last_name,
          email: regForm.email,
          phone: regForm.phone || undefined,
          role: regForm.role,
          password: regForm.password,
        },
        vendorFields,
      );
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Registration failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function handleForgot(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await api.forgotPassword(forgotEmail);
      setNotice(response.message);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-pattern min-h-screen flex items-center justify-center p-4 font-sans">
      <div className="w-full max-w-[560px]">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-container rounded-xl mb-3">
            <svg className="w-6 h-6 text-on-primary-container" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/>
            </svg>
          </div>
          <h1 className="font-display-lg text-display-lg text-primary">VendorBridge</h1>
          <p className="text-body-base text-on-surface-variant mt-1">
            {mode === "login"
              ? "Sign in to your enterprise procurement portal"
              : mode === "register"
                ? "Complete your registration to access the platform"
                : "Reset your account access"}
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel rounded-2xl p-8">
          {error && (
            <div className="mb-5 rounded-lg bg-error-container border border-error/20 px-4 py-3 text-sm text-on-error-container">
              {error}
            </div>
          )}
          {notice && (
            <div className="mb-5 rounded-lg bg-secondary-container/40 border border-secondary/20 px-4 py-3 text-sm text-on-secondary-container">
              {notice}
            </div>
          )}

          {/* LOGIN FORM */}
          {mode === "login" && (
            <form onSubmit={handleLogin} className="flex flex-col gap-5">
              <div className="flex flex-col gap-1.5">
                <label className="label" htmlFor="login-email">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={18} />
                  <input
                    id="login-email"
                    className="field pl-10"
                    type="email"
                    placeholder="Enter your email"
                    value={loginForm.email}
                    onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <label className="label" htmlFor="login-password">Password</label>
                  <button
                    type="button"
                    className="text-xs font-semibold text-secondary hover:text-primary transition-colors"
                    onClick={() => { setMode("forgot"); setError(null); }}
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={18} />
                  <input
                    id="login-password"
                    className="field pl-10 pr-10"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-2.5 text-on-surface-variant hover:text-on-surface transition-colors"
                    onClick={() => setShowPassword((v) => !v)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                className="w-full h-12 bg-primary-container text-on-primary-container font-semibold rounded-xl shadow-sm hover:bg-primary hover:text-on-primary transition-colors flex items-center justify-center gap-2 mt-1"
                disabled={busy}
              >
                {busy ? "Signing in…" : "Sign In"}
              </button>
              <p className="text-center text-sm text-on-surface-variant">
                Don&apos;t have an account?{" "}
                <button
                  type="button"
                  className="font-semibold text-primary hover:underline transition-colors"
                  onClick={() => { setMode("register"); setError(null); }}
                >
                  Register here
                </button>
              </p>
            </form>
          )}

          {/* REGISTRATION FORM */}
          {mode === "register" && (
            <form onSubmit={handleRegister} className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-4">
              <div className="md:col-span-2">
                <h2 className="font-headline-md text-headline-md text-on-surface mb-1">Create Account</h2>
                <p className="text-body-dense text-on-surface-variant">Fill in your details to join VendorBridge IQ</p>
              </div>

              {/* Role select (shown first to conditionally show vendor fields) */}
              <div className="md:col-span-2 flex flex-col gap-1">
                <label className="label" htmlFor="reg-role">Account Role</label>
                <select
                  id="reg-role"
                  className="field"
                  value={regForm.role}
                  onChange={(e) => setRegForm({ ...regForm, role: e.target.value as UserRole })}
                  required
                >
                  {ROLE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Vendor company info */}
              {isVendor && (
                <>
                  <div className="md:col-span-2">
                    <div className="rounded-lg bg-secondary-container/20 border border-secondary/20 px-4 py-3">
                      <p className="text-sm font-semibold text-on-secondary-container">Vendor Registration</p>
                      <p className="text-xs text-on-surface-variant mt-0.5">Please provide your company and compliance details</p>
                    </div>
                  </div>
                  <div className="md:col-span-2 flex flex-col gap-1">
                    <label className="label" htmlFor="reg-company">Company Name *</label>
                    <input
                      id="reg-company"
                      className="field"
                      placeholder="Your company / business name"
                      value={regForm.company_name}
                      onChange={(e) => setRegForm({ ...regForm, company_name: e.target.value })}
                      required={isVendor}
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="label" htmlFor="reg-gstin">GST Number (GSTIN) *</label>
                    <input
                      id="reg-gstin"
                      className="field uppercase"
                      placeholder="e.g. 24ABCDE1234F1Z5"
                      maxLength={15}
                      minLength={15}
                      value={regForm.gstin}
                      onChange={(e) => setRegForm({ ...regForm, gstin: e.target.value.toUpperCase() })}
                      required={isVendor}
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="label" htmlFor="reg-pan">PAN Number</label>
                    <input
                      id="reg-pan"
                      className="field uppercase"
                      placeholder="e.g. ABCDE1234F"
                      maxLength={10}
                      value={regForm.pan}
                      onChange={(e) => setRegForm({ ...regForm, pan: e.target.value.toUpperCase() })}
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="label" htmlFor="reg-state">State *</label>
                    <select
                      id="reg-state"
                      className="field"
                      value={regForm.state}
                      onChange={(e) => setRegForm({ ...regForm, state: e.target.value })}
                      required={isVendor}
                    >
                      {INDIA_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="label" htmlFor="reg-city">City *</label>
                    <input
                      id="reg-city"
                      className="field"
                      placeholder="e.g. Ahmedabad"
                      value={regForm.city}
                      onChange={(e) => setRegForm({ ...regForm, city: e.target.value })}
                      required={isVendor}
                    />
                  </div>
                  <div className="md:col-span-2 flex flex-col gap-1">
                    <label className="label" htmlFor="reg-category">Product Category *</label>
                    <select
                      id="reg-category"
                      className="field"
                      value={regForm.category_name}
                      onChange={(e) => setRegForm({ ...regForm, category_name: e.target.value })}
                      required={isVendor}
                    >
                      {PRODUCT_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  {/* Bank Information */}
                  <div className="md:col-span-2">
                    <p className="label mb-2">Bank Information</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="flex flex-col gap-1">
                        <label className="label" htmlFor="reg-bank-name">Account Holder Name</label>
                        <input
                          id="reg-bank-name"
                          className="field"
                          placeholder="As per bank records"
                          value={regForm.bank_account_name}
                          onChange={(e) => setRegForm({ ...regForm, bank_account_name: e.target.value })}
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="label" htmlFor="reg-bank-number">Account Number</label>
                        <input
                          id="reg-bank-number"
                          className="field"
                          placeholder="Bank account number"
                          value={regForm.bank_account_number}
                          onChange={(e) => setRegForm({ ...regForm, bank_account_number: e.target.value })}
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="label" htmlFor="reg-ifsc">IFSC Code</label>
                        <input
                          id="reg-ifsc"
                          className="field uppercase"
                          placeholder="e.g. SBIN0001234"
                          value={regForm.ifsc_code}
                          onChange={(e) => setRegForm({ ...regForm, ifsc_code: e.target.value.toUpperCase() })}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Contact / personal fields */}
              <div className="flex flex-col gap-1">
                <label className="label" htmlFor="reg-first">{isVendor ? "Contact First Name *" : "First Name *"}</label>
                <input
                  id="reg-first"
                  className="field"
                  placeholder="First name"
                  value={regForm.first_name}
                  onChange={(e) => setRegForm({ ...regForm, first_name: e.target.value })}
                  required
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="label" htmlFor="reg-last">{isVendor ? "Contact Last Name *" : "Last Name *"}</label>
                <input
                  id="reg-last"
                  className="field"
                  placeholder="Last name"
                  value={regForm.last_name}
                  onChange={(e) => setRegForm({ ...regForm, last_name: e.target.value })}
                  required
                />
              </div>
              <div className="md:col-span-2 flex flex-col gap-1">
                <label className="label" htmlFor="reg-email">Email Address *</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={18} />
                  <input
                    id="reg-email"
                    className="field pl-10"
                    type="email"
                    placeholder="your@email.com"
                    value={regForm.email}
                    onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="label" htmlFor="reg-phone">Phone Number</label>
                <input
                  id="reg-phone"
                  className="field"
                  type="tel"
                  placeholder="+91 98765 43210"
                  value={regForm.phone}
                  onChange={(e) => setRegForm({ ...regForm, phone: e.target.value })}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="label" htmlFor="reg-password">Password *</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={18} />
                  <input
                    id="reg-password"
                    className="field pl-10 pr-10"
                    type={showPassword ? "text" : "password"}
                    placeholder="Min. 8 characters"
                    minLength={8}
                    value={regForm.password}
                    onChange={(e) => setRegForm({ ...regForm, password: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-2.5 text-on-surface-variant hover:text-on-surface"
                    onClick={() => setShowPassword((v) => !v)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label className="label" htmlFor="reg-confirm">Confirm Password *</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={18} />
                  <input
                    id="reg-confirm"
                    className="field pl-10"
                    type={showPassword ? "text" : "password"}
                    placeholder="Repeat your password"
                    minLength={8}
                    value={regForm.confirm_password}
                    onChange={(e) => setRegForm({ ...regForm, confirm_password: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="md:col-span-2 mt-2">
                <button
                  type="submit"
                  className="w-full h-12 bg-primary-container text-on-primary-container font-semibold rounded-xl shadow-sm hover:bg-primary hover:text-on-primary transition-colors flex items-center justify-center gap-2"
                  disabled={busy}
                >
                  {busy ? "Creating account…" : (
                    <>
                      <User size={18} />
                      Complete Registration
                    </>
                  )}
                </button>
              </div>
              <p className="md:col-span-2 text-center text-sm text-on-surface-variant">
                Already have an account?{" "}
                <button
                  type="button"
                  className="font-semibold text-primary hover:underline"
                  onClick={() => { setMode("login"); setError(null); }}
                >
                  Log in here
                </button>
              </p>
            </form>
          )}

          {/* FORGOT PASSWORD FORM */}
          {mode === "forgot" && (
            <form onSubmit={handleForgot} className="flex flex-col gap-5">
              <div>
                <h2 className="font-headline-md text-headline-md text-on-surface mb-1">Reset Password</h2>
                <p className="text-body-dense text-on-surface-variant">Enter your email to receive a reset link</p>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="label" htmlFor="forgot-email">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 text-on-surface-variant pointer-events-none" size={18} />
                  <input
                    id="forgot-email"
                    className="field pl-10"
                    type="email"
                    placeholder="your@email.com"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                  />
                </div>
              </div>
              <button
                type="submit"
                className="w-full h-12 bg-primary-container text-on-primary-container font-semibold rounded-xl shadow-sm hover:bg-primary hover:text-on-primary transition-colors"
                disabled={busy}
              >
                {busy ? "Sending…" : "Request Reset"}
              </button>
              <p className="text-center text-sm text-on-surface-variant">
                Remember your password?{" "}
                <button
                  type="button"
                  className="font-semibold text-primary hover:underline"
                  onClick={() => { setMode("login"); setError(null); setNotice(null); }}
                >
                  Sign in
                </button>
              </p>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-center gap-5 mt-6 text-xs text-on-surface-variant">
          <span>Privacy Policy</span>
          <span>•</span>
          <span>Terms of Service</span>
          <span>•</span>
          <span>BuzzBeatStrong · Odoo Hackathon</span>
        </div>
      </div>
    </div>
  );
}
