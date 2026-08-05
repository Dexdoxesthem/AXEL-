"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginForm() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        router.push("/");
        router.refresh();
      } else {
        setError("Incorrect password. Please try again.");
        setBusy(false);
      }
    } catch {
      setError("Could not reach the server.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <label className="caps" htmlFor="password" style={{ display: "block", marginBottom: 6 }}>
        System password
      </label>
      <input
        id="password"
        name="password"
        type="password"
        className="text-input"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="enter password"
        autoFocus
      />
      {error && (
        <p style={{ color: "var(--primary)", margin: "10px 0 0" }}>
          <strong>{error}</strong>
        </p>
      )}
      <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
        <button className="btn btn--primary" type="submit" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
      </div>
    </form>
  );
}
