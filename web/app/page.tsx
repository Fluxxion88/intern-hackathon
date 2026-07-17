"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/Button";
import { HeroLedger } from "@/components/HeroLedger";

const TRUTHS: { title: string; body: string }[] = [
  {
    title: "It learns from your file, not your explanation.",
    body: "You give it two you started with and one you finished. That's the whole specification. It practises against your own work until it matches, and it tells you the number.",
  },
  {
    title: "What you get back has no AI inside it.",
    body: "Once it has learned the job, the intelligence is thrown away. What runs every morning is a plain, boring program. It does the same thing every time, in about a second, and it can't invent anything.",
  },
  {
    title: "It tells you what it can't do.",
    body: "If it only ever gets to 87%, it says 87%, and it marks the rows it wasn't sure about. You finish those three. You still got your morning back.",
  },
];

export default function LandingPage() {
  const router = useRouter();
  return (
    <div style={{ minHeight: "100vh", background: "var(--paper-0)" }}>
      <header>
        <div
          className="container"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            height: 56,
          }}
        >
          <span className="label" style={{ color: "var(--ink-900)" }}>
            Intern
          </span>
          <Link
            href="/start"
            className="body-text"
            style={{ color: "var(--ink-500)", textDecoration: "none", borderRadius: "var(--r-1)", padding: "var(--s-1) var(--s-2)" }}
          >
            Sign in
          </Link>
        </div>
        <div style={{ borderBottom: "var(--rule-thin)" }} />
      </header>

      <main className="container" style={{ paddingTop: "var(--s-9)", paddingBottom: "var(--s-9)" }}>
        <h1 className="display-1 measure">
          Train an intern to do
          <br />
          the boring half of your job.
        </h1>

        <p className="body-text measure" style={{ color: "var(--ink-500)", marginTop: "var(--s-5)" }}>
          You explain it once, the way you&apos;d explain it to a new hire. You show it one you
          did earlier. It practises until it matches. Then it works for you, forever, at a web
          address of your own.
        </p>

        <div style={{ display: "flex", gap: "var(--s-3)", marginTop: "var(--s-6)", flexWrap: "wrap" }}>
          <Button onClick={() => router.push("/train/new")}>Train your first one</Button>
          <Button variant="secondary" onClick={() => router.push("/train/demo/training")}>
            Watch a 60-second one
          </Button>
        </div>

        <p className="label" style={{ color: "var(--ink-500)", marginTop: "var(--s-5)" }}>
          No installing. No subscription. $20 once, per intern.
        </p>

        <div style={{ marginTop: "var(--s-8)", maxWidth: 720 }}>
          <HeroLedger />
        </div>

        <div style={{ borderTop: "var(--rule-thin)", margin: "var(--s-9) 0 var(--s-7)" }} />

        <div className="label" style={{ color: "var(--ink-500)", marginBottom: "var(--s-6)" }}>
          Three things that are true
        </div>

        <div className="truths-grid">
          {TRUTHS.map((t) => (
            <div key={t.title}>
              <h2 className="title-2" style={{ maxWidth: "62ch" }}>
                {t.title}
              </h2>
              <p className="body-text" style={{ color: "var(--ink-500)", marginTop: "var(--s-3)", maxWidth: "62ch" }}>
                {t.body}
              </p>
            </div>
          ))}
        </div>

        <div style={{ borderTop: "var(--rule-thin)", margin: "var(--s-9) 0 var(--s-6)" }} />

        <p className="label" style={{ color: "var(--ink-300)" }}>
          Built at the Loop Engineering Hackathon · AWS Builder Loft · July 2026
        </p>
      </main>
    </div>
  );
}
