"use client";

export const dynamic = "force-dynamic";

import Link from "next/link";

export default function ArticlesPage() {
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

      <div className="max-w-2xl mx-auto px-6 sm:px-10 py-32 text-center">
        <p
          className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-5"
          style={{ color: "#D4725C" }}
        >
          Articles
        </p>
        <h1
          className="text-[36px] sm:text-[48px] leading-[1.1] tracking-[-0.02em] mb-6"
          style={{ fontFamily: "'Fraunces', Georgia, serif", fontWeight: 500, color: "#1A2540" }}
        >
          Coming{" "}
          <span style={{ fontStyle: "italic", color: "#D4725C" }}>soon</span>
        </h1>
        <p className="text-[16px] leading-[1.65] mb-10" style={{ color: "#6B6560" }}>
          We&rsquo;re writing the first batch of articles with our doctors right now.
          Expect honest, plain-language pieces on the things Ethiopian patients actually ask us about.
        </p>
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
  );
}
