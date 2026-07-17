"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sheet } from "@/components/Sheet";
import { Button } from "@/components/Button";
import { Field } from "@/components/Field";
import { apiPost, MOCK_FLAG } from "@/lib/api";

export default function StartPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const go = async () => {
    if (!name.trim()) {
      setProblem("Put your first name in — your intern needs to know who it works for.");
      return;
    }
    setProblem(null);
    setSending(true);
    if (!MOCK_FLAG) {
      try {
        await apiPost(`/api/session`, { name: name.trim(), email: email.trim() });
      } catch {
        // Mocked sign-in continues regardless.
      }
    }
    router.push("/train/new");
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--paper-0)", display: "flex", flexDirection: "column" }}>
      <header>
        <div className="container" style={{ display: "flex", alignItems: "center", height: 56 }}>
          <Link
            href="/"
            className="label"
            style={{ color: "var(--ink-900)", textDecoration: "none", borderRadius: "var(--r-1)" }}
          >
            Intern
          </Link>
        </div>
        <div style={{ borderBottom: "var(--rule-thin)" }} />
      </header>

      <main
        style={{
          flex: "1 1 auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "var(--s-6) var(--s-4)",
        }}
      >
        <div style={{ width: "100%", maxWidth: 420 }}>
          <Sheet style={{ padding: "var(--s-6)" }}>
            <h1 className="title-1" style={{ marginBottom: "var(--s-5)" }}>
              Let&apos;s get you started.
            </h1>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                go();
              }}
              style={{ display: "flex", flexDirection: "column", gap: "var(--s-4)" }}
            >
              <Field
                label="Your name"
                value={name}
                onChange={setName}
                placeholder="Andrei"
                help="So your intern knows who it works for."
                error={problem ?? undefined}
              />
              <Field
                label="Work email"
                type="email"
                value={email}
                onChange={setEmail}
                placeholder="andrei@"
                help="We send the web address here when it's trained. Nothing else."
              />
              <Button type="submit" full disabled={sending}>
                Continue
              </Button>
            </form>
          </Sheet>
          <p className="label" style={{ color: "var(--ink-500)", textAlign: "center", marginTop: "var(--s-4)" }}>
            No password. We&apos;ll email you a link.
          </p>
        </div>
      </main>
    </div>
  );
}
