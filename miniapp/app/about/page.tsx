"use client";

export const dynamic = "force-dynamic";

import Link from "next/link";

export default function AboutPage() {
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

      <div className="max-w-3xl mx-auto px-6 sm:px-10 py-24 sm:py-32">
        <p
          className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-5"
          style={{ color: "#D4725C" }}
        >
          About
        </p>
        <h1
          className="text-[40px] sm:text-[56px] leading-[1.05] tracking-[-0.02em] mb-8"
          style={{ fontFamily: "'Fraunces', Georgia, serif", fontWeight: 500, color: "#1A2540" }}
        >
          Healthcare,{" "}
          <span style={{ fontStyle: "italic", color: "#D4725C" }}>without the friction</span>
        </h1>

        <div className="space-y-6 text-[17px] leading-[1.75]" style={{ color: "#3A4560" }}>
          <p>
            LongiMed exists because reaching a verified Ethiopian doctor shouldn&rsquo;t require a queue,
            a long drive, or a question you&rsquo;re too embarrassed to ask in person.
          </p>
          <p>
            We connect patients with licensed physicians on the platform they already use every day —
            Telegram. Free public Q&amp;A for community questions. Private, anonymous-if-you-want
            consultations for everything else. Emergency guidance the moment you describe symptoms
            that need it.
          </p>
          <p>
            Our doctors are real, vetted, and accountable. Our pricing is honest. Our mission is to
            make good care feel ordinary in Ethiopia.
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
