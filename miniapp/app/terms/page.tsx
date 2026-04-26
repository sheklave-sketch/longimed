"use client";

export const dynamic = "force-dynamic";

import Link from "next/link";

export default function TermsPage() {
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
          Terms
        </p>
        <h1
          className="text-[36px] sm:text-[44px] leading-[1.1] tracking-[-0.02em] mb-8"
          style={{ fontFamily: "'Fraunces', Georgia, serif", fontWeight: 500, color: "#1A2540" }}
        >
          A few honest ground rules
        </h1>

        <div className="space-y-5 text-[15px] leading-[1.75]" style={{ color: "#3A4560" }}>
          <p>
            LongiMed connects you with verified doctors for general guidance. We are not a
            substitute for emergency care — if you suspect a medical emergency, call{" "}
            <span style={{ color: "#1A2540", fontWeight: 600 }}>907</span>,{" "}
            <span style={{ color: "#1A2540", fontWeight: 600 }}>991</span>, or{" "}
            <span style={{ color: "#1A2540", fontWeight: 600 }}>939</span> immediately.
          </p>
          <p>
            Consultations are confidential between you and the consulting doctor. Be honest about
            symptoms, medications, and history — accurate input means accurate guidance.
          </p>
          <p>
            Full terms of service are being finalized. For specific questions, email{" "}
            <a href="mailto:legal@longimed.com" style={{ color: "#35C8BB", fontWeight: 600 }}>
              legal@longimed.com
            </a>
            .
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
