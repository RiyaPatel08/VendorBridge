import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, type RegisterPayload, type VendorRegistrationFields } from "../../lib/api";
import type { User } from "../../lib/types";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload, vendorFields?: VendorRegistrationFields) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const TOKEN_KEY = "vendorbridge.token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      loading,
      login: async (email: string, password: string) => {
        const response = await api.login(email, password);
        localStorage.setItem(TOKEN_KEY, response.access_token);
        setToken(response.access_token);
        setUser(response.user);
      },
      register: async (payload: RegisterPayload, vendorFields?: VendorRegistrationFields) => {
        const response = await api.register(payload);
        localStorage.setItem(TOKEN_KEY, response.access_token);

        // If vendor role, auto-create vendor profile
        if (payload.role === "vendor" && vendorFields) {
          try {
            const categories = await api.categories(response.access_token);
            const matchedCategory =
              categories.find(
                (c) => c.name.toLowerCase() === vendorFields.category_name.toLowerCase(),
              ) ?? categories[0];
            const categoryId = matchedCategory?.id ?? 1;

            await api.createVendor(response.access_token, {
              name: vendorFields.company_name,
              legal_name: vendorFields.company_name,
              category_id: categoryId,
              gstin: vendorFields.gstin,
              pan: vendorFields.pan,
              state: vendorFields.state,
              city: vendorFields.city,
              contact_name: `${payload.first_name} ${payload.last_name}`,
              contact_email: payload.email,
              contact_phone: payload.phone ?? "",
              status: "pending",
              completed_orders_count: 0,
              rating: "0.00",
              reliability_score: "0.00",
              delivery_score: "0.00",
              completion_rate: "0.00",
              satisfaction_score: "0.00",
              compliance_notes: vendorFields.bank_details
                ? `Bank Details: ${vendorFields.bank_details}`
                : undefined,
            });
          } catch (err) {
            // Vendor profile creation failed — user account was still created
            console.error("Vendor profile creation failed:", err);
          }
        }

        setToken(response.access_token);
        setUser(response.user);
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      },
    }),
    [loading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
