import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError, type Me } from "../api";

const MESSAGES: Record<string, string> = {
  invalid_credentials: "That email and passphrase don’t match.",
  rate_limited: "Too many tries. Please wait a bit and try again.",
  email_taken: "An account with that email already exists. Try signing in.",
  weak_passphrase: "Use a passphrase of at least 12 characters.",
  invalid_email: "Please enter a valid email address.",
  google_cancelled: "Google sign-in was cancelled.",
};

export default function Login({ onSignedIn }: { onSignedIn: (me: Me) => void }) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [cfg, setCfg] = useState<{ google: boolean; local_signup: boolean }>({ google: false, local_signup: true });

  useEffect(() => {
    api.config().then(setCfg).catch(() => undefined);
    const err = new URLSearchParams(location.search).get("error");
    if (err) setError(MESSAGES[err] || "Sign-in failed. Please try again.");
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = mode === "signin" ? await api.login(email, pass) : await api.signup(email, pass);
      onSignedIn(me);
    } catch (err) {
      const code = err instanceof ApiError ? err.code : "error";
      setError(MESSAGES[code] || "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card narrow">
      <h1>{mode === "signin" ? "Sign in" : "Create your account"}</h1>
      {cfg.google && (
        <>
          <a className="btn google" href="/api/auth/google/start" data-track="auth.google">Continue with Google</a>
          <p className="or">or use email</p>
        </>
      )}
      <form onSubmit={submit}>
        <label>Email<input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label>
          Passphrase
          <input type="password" autoComplete={mode === "signin" ? "current-password" : "new-password"} minLength={mode === "signup" ? 12 : undefined} value={pass} onChange={(e) => setPass(e.target.value)} required />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn primary" disabled={busy} data-track={mode === "signin" ? "auth.signin" : "auth.signup"}>
          {mode === "signin" ? "Sign in" : "Create account"}
        </button>
      </form>
      {cfg.local_signup && (
        <button className="link" onClick={() => setMode(mode === "signin" ? "signup" : "signin")} data-track="auth.toggle">
          {mode === "signin" ? "New here? Create an account" : "Have an account? Sign in"}
        </button>
      )}
      <p className="fine">We keep only your email, a display name and a handle. No ads, no third-party trackers.</p>
    </section>
  );
}
