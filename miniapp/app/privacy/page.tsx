"use client";

export const dynamic = "force-dynamic";

import Link from "next/link";

export default function PrivacyPage() {
  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      style={{
        background: "#FFFBF7",
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
        color: "#1A2540",
      }}
    >
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
      `}</style>

      <div className="max-w-2xl mx-auto px-6 sm:px-10 py-24 sm:py-32">
        <p
          className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-5"
          style={{ color: "#D4725C" }}
        >
          Privacy
        </p>
        <h1
          className="text-[36px] sm:text-[44px] leading-[1.1] tracking-[-0.02em] mb-8"
          style={{ fontFamily: "'Fraunces', Georgia, serif", fontWeight: 500, color: "#1A2540" }}
        >
          Your health data, treated with care
        </h1>

        <div className="space-y-5 text-[15px] leading-[1.75]" style={{ color: "#3A4560" }}>
          <p>
            We&rsquo;re finalizing our full privacy notice. The short version: we collect only what we
            need to connect you with a doctor, we never sell your data, and you can request deletion
            of your account and history at any time.
          </p>
          <p>
            Anonymous consultation mode means doctors only see what you write — not your name, your
            phone number, or your Telegram profile.
          </p>
          <p>
            Until the full policy is published, email{" "}
            <a href="mailto:privacy@longimed.com" style={{ color: "#35C8BB", fontWeight: 600 }}>
              privacy@longimed.com
            </a>{" "}
            with any specific questions.
          </p>
        </div>

        <div className="mt-12">
          <Link
            href="/landing"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full font-semibold text-[14px] text-white transition-transform active:scale-[0.97]"
            style={{ background: "#1A2540" }}
          >
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
