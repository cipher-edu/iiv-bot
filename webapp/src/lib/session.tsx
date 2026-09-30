"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { BadgeItem, Certificate, Course, LeaderboardUser, TestItem, UserProfile } from "@/types";
import { api, ApiError, setToken } from "@/lib/api";
import { getTelegramWebApp, triggerHaptic } from "@/lib/telegram";

interface Bootstrap {
  user: UserProfile;
  courses: Course[];
  tests: TestItem[];
  leaderboard: LeaderboardUser[];
  badges: BadgeItem[];
  certificates: Certificate[];
}

interface SessionValue extends Bootstrap {
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  logout: () => void;
}

const empty: Bootstrap = {
  user: null as unknown as UserProfile,
  courses: [],
  tests: [],
  leaderboard: [],
  badges: [],
  certificates: [],
};

const SessionContext = createContext<SessionValue | null>(null);

export function useSession() {
  const value = useContext(SessionContext);
  if (!value) {
    throw new Error("useSession SessionProvider ichida ishlatiladi");
  }
  return value;
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);

  const load = useCallback(async () => {
    const payload = await api<Bootstrap>("/api/v1/bootstrap");
    setData(payload);
    setNeedsLogin(false);
    setError(null);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      setLoading(true);
      try {
        const tg = getTelegramWebApp();
        const initData = tg?.initData || "";
        if (initData) {
          const auth = await api<{ token: string }>("/api/v1/auth/telegram", {
            method: "POST",
            body: JSON.stringify({ initData }),
          });
          setToken(auth.token);
        }
        if (!cancelled) await load();
      } catch (err) {
        if (cancelled) return;
        const status = err instanceof ApiError ? err.status : 0;
        if (status === 401 || status === 0) {
          setToken(null);
          setNeedsLogin(true);
          setError(null);
        } else {
          setError(err instanceof Error ? err.message : "Yuklashda xato");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    boot();
    return () => {
      cancelled = true;
    };
  }, [load]);

  const logout = useCallback(() => {
    setToken(null);
    setData(null);
    setNeedsLogin(true);
  }, []);

  const refresh = useCallback(async () => {
    await load();
  }, [load]);

  const value = useMemo<SessionValue>(
    () => ({
      ...(data || empty),
      loading,
      error,
      refresh,
      logout,
    }),
    [data, loading, error, refresh, logout]
  );

  return (
    <SessionContext.Provider value={value}>
      {loading ? (
        <BootScreen label="IIV EduBot yuklanmoqda" />
      ) : needsLogin || !data || needsCategory(data.user) ? (
        <AuthScreen
          error={error}
          onSuccess={async () => {
            setLoading(true);
            try {
              await load();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Kirishda xato");
            } finally {
              setLoading(false);
            }
          }}
        />
      ) : (
        children
      )}
    </SessionContext.Provider>
  );
}

function BootScreen({ label }: { label: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm text-center space-y-3">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-primary/15 text-primary flex items-center justify-center text-xl font-black">
          IIV
        </div>
        <p className="text-sm font-semibold text-foreground">{label}</p>
        <div className="h-1.5 w-28 mx-auto rounded-full bg-secondary overflow-hidden">
          <div className="h-full w-1/2 bg-primary animate-pulse" />
        </div>
      </div>
    </div>
  );
}

const STAFF = new Set(["superadmin"]);

function needsCategory(user: UserProfile | null) {
  if (!user) return false;
  if (STAFF.has(user.role)) return false;
  return !user.category;
}

function AuthScreen({
  error,
  onSuccess,
}: {
  error: string | null;
  onSuccess: () => Promise<void>;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [position, setPosition] = useState("");
  const [category, setCategory] = useState<"hodim" | "fuqaro">("fuqaro");
  const [pending, setPending] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setLocalError(null);
    const initData = getTelegramWebApp()?.initData || "";
    try {
      const path = mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register";
      const body =
        mode === "login"
          ? { login, password, initData }
          : { login, password, fullName, phone, position, category, initData };
      const auth = await api<{ token: string }>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setToken(auth.token);
      triggerHaptic("success");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Amal bajarilmadi");
      triggerHaptic("error");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-8">
      <form
        onSubmit={submit}
        className="w-full max-w-md bg-card border border-border/70 rounded-3xl p-6 shadow-xl space-y-4"
      >
        <div className="space-y-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-primary">IIV EduBot</p>
          <h1 className="text-xl font-black text-foreground">
            {mode === "login" ? "Kirish" : "Ro'yxatdan o'tish"}
          </h1>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Eski hisob login va parol bilan kiradi. Yangi hisob hodim yoki fuqaro sifatida ochiladi.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`py-2.5 rounded-xl border font-semibold ${
              mode === "login"
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-secondary/50 border-border/60"
            }`}
          >
            Kirish
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`py-2.5 rounded-xl border font-semibold ${
              mode === "register"
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-secondary/50 border-border/60"
            }`}
          >
            Ro&apos;yxatdan o&apos;tish
          </button>
        </div>
        {mode === "register" && (
          <>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {(
                [
                  ["hodim", "Hodim"],
                  ["fuqaro", "Fuqaro"],
                ] as const
              ).map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  onClick={() => setCategory(value)}
                  className={`py-2.5 rounded-xl border font-semibold ${
                    category === value
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-secondary/50 border-border/60"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <label className="block space-y-1 text-xs">
              <span className="font-semibold">F.I.O.</span>
              <input
                required
                minLength={3}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className="font-semibold">Telefon</span>
              <input
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
                placeholder="+998"
              />
            </label>
            {category === "hodim" && (
              <label className="block space-y-1 text-xs">
                <span className="font-semibold">Lavozim</span>
                <input
                  value={position}
                  onChange={(e) => setPosition(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
                />
              </label>
            )}
          </>
        )}
        <label className="block space-y-1 text-xs">
          <span className="font-semibold">Login</span>
          <input
            required
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
          />
        </label>
        <label className="block space-y-1 text-xs">
          <span className="font-semibold">Parol</span>
          <input
            required
            type="password"
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
          />
        </label>
        {(localError || error) && <p className="text-xs text-red-400">{localError || error}</p>}
        <button
          type="submit"
          disabled={pending}
          className="w-full py-3 rounded-2xl bg-primary text-primary-foreground text-sm font-bold disabled:opacity-50"
        >
          {pending ? "Kutilmoqda..." : mode === "login" ? "Kirish" : "Ro'yxatdan o'tish"}
        </button>
      </form>
    </div>
  );
}

function LocalLogin({
  error,
  onSuccess,
}: {
  error: string | null;
  onSuccess: () => Promise<void>;
}) {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [category, setCategory] = useState<"hodim" | "fuqaro">("hodim");
  const [pending, setPending] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setLocalError(null);
    try {
      const auth = await api<{ token: string }>("/api/v1/auth/local", {
        method: "POST",
        body: JSON.stringify({ fullName, phone, category }),
      });
      setToken(auth.token);
      triggerHaptic("success");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Kirishda xato");
      triggerHaptic("error");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-8">
      <form
        onSubmit={submit}
        className="w-full max-w-md bg-card border border-border/70 rounded-3xl p-6 shadow-xl space-y-4"
      >
        <div className="space-y-1">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-primary">
            Telegram Web App
          </p>
          <h1 className="text-xl font-black text-foreground">IIV EduBot</h1>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Telegram ichida ochilsa, hisob avtomatik taniladi. Brauzerda ism-familiya bilan kiring.
          </p>
        </div>

        <label className="block space-y-1 text-xs">
          <span className="font-semibold text-foreground">F.I.O.</span>
          <input
            required
            minLength={3}
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
            placeholder="Ism familiya"
          />
        </label>

        <label className="block space-y-1 text-xs">
          <span className="font-semibold text-foreground">Telefon</span>
          <input
            value={phone}
            maxLength={20}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl bg-secondary/70 border border-border/60 text-sm"
            placeholder="+998"
          />
        </label>

        <div className="grid grid-cols-2 gap-2 text-xs">
          {(
            [
              ["hodim", "Xodim"],
              ["fuqaro", "Fuqaro"],
            ] as const
          ).map(([value, label]) => (
            <button
              type="button"
              key={value}
              onClick={() => setCategory(value)}
              className={`py-2.5 rounded-xl border font-semibold ${
                category === value
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-secondary/50 border-border/60 text-foreground"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {(localError || error) && (
          <p className="text-xs text-red-400">{localError || error}</p>
        )}

        <button
          type="submit"
          disabled={pending}
          className="w-full py-3 rounded-2xl bg-primary text-primary-foreground text-sm font-bold disabled:opacity-50"
        >
          {pending ? "Kirilmoqda..." : "Platformaga kirish"}
        </button>
      </form>
    </div>
  );
}
