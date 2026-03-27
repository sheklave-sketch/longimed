"use client";

import { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { initTelegram } from "@/lib/telegram";

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.16, 1, 0.3, 1] },
});

const STEPS = [
  {
    num: "01",
    icon: "💬",
    title: "Ask a Question",
    desc: "Post your health question anonymously. Our verified doctors answer on the public Q&A channel — free for everyone.",
    accent: "bg-brand-teal",
  },
  {
    num: "02",
    icon: "📋",
    title: "Book a Consultation",
    desc: "Need privacy? Book a 1-on-1 session with any available doctor. Choose anonymous relay or direct messaging.",
    accent: "bg-brand-blue",
  },
  {
    num: "03",
    icon: "✅",
    title: "Get Expert Care",
    desc: "Receive personalized medical guidance from licensed Ethiopian doctors. Follow up until your concern is resolved.",
    accent: "bg-emerald-500",
  },
];

const SERVICES = [
  {
    icon: "🩺",
    title: "Public Q&A",
    desc: "Free community health answers from verified doctors. Ask anything, stay anonymous.",
    tag: "Free",
    tagColor: "bg-emerald-50 text-emerald-700",
    href: "/qa",
  },
  {
    icon: "🔒",
    title: "Private Consultation",
    desc: "Confidential 1-on-1 sessions. Choose your doctor, describe your issue, get dedicated care.",
    tag: "From 0 ETB",
    tagColor: "bg-brand-teal-light text-brand-teal-deep",
    href: "/book",
  },
  {
    icon: "🚨",
    title: "Emergency Guidance",
    desc: "Chest pain? Difficulty breathing? Our bot instantly connects you with emergency numbers and nearest hospitals.",
    tag: "24/7",
    tagColor: "bg-rose-50 text-rose-700",
    href: null,
  },
];

export default function HomePage() {
  useEffect(() => {
    initTelegram();
  }, []);

  return (
    <div className="pt-2 pb-12 -mx-5">
      {/* ── Hero ── */}
      <section className="px-5 pt-6 pb-10 relative overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-brand-teal/[0.06] blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-16 w-48 h-48 rounded-full bg-brand-blue/[0.05] blur-2xl pointer-events-none" />

        <motion.div {...fadeUp(0)} className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-teal-light border border-brand-teal/20 mb-5">
            <span className="status-online" />
            <span className="text-[12px] font-semibold text-brand-teal-deep tracking-wide">Doctors available now</span>
          </div>
        </motion.div>

        <motion.h1
          {...fadeUp(0.08)}
          className="relative font-display font-bold text-[32px] leading-[1.15] tracking-tight text-ink-rich mb-3"
        >
          Your health,{" "}
          <span className="text-gradient">one tap away</span>
        </motion.h1>

        <motion.p {...fadeUp(0.14)} className="relative text-ink-secondary text-[15px] leading-relaxed max-w-[320px] mb-7">
          Connect with verified Ethiopian doctors for free Q&A, private consultations, and emergency guidance — all through Telegram.
        </motion.p>

        <motion.div {...fadeUp(0.2)} className="relative flex gap-3">
          <Link
            href="/doctors"
            className="flex-1 text-center py-3.5 rounded-2xl bg-gradient-teal text-white font-display font-bold text-[14px] shadow-glow active:scale-[0.97] transition-transform"
          >
            Browse Doctors
          </Link>
          <Link
            href="/book"
            className="flex-1 text-center py-3.5 rounded-2xl bg-surface-white border border-surface-border text-ink-rich font-display font-bold text-[14px] hover:border-brand-teal/30 active:scale-[0.97] transition-all"
          >
            Book Now
          </Link>
        </motion.div>

        {/* Trust indicators */}
        <motion.div {...fadeUp(0.28)} className="relative flex items-center justify-center gap-6 mt-8 pt-6 border-t border-surface-border">
          <div className="text-center">
            <p className="font-display font-bold text-[20px] text-ink-rich">100%</p>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider mt-0.5">Verified</p>
          </div>
          <div className="w-px h-8 bg-surface-border" />
          <div className="text-center">
            <p className="font-display font-bold text-[20px] text-ink-rich">24/7</p>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider mt-0.5">Available</p>
          </div>
          <div className="w-px h-8 bg-surface-border" />
          <div className="text-center">
            <p className="font-display font-bold text-[20px] text-ink-rich">Free</p>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider mt-0.5">Q&A</p>
          </div>
        </motion.div>
      </section>

      {/* ── How It Works ── */}
      <section className="px-5 py-8">
        <motion.div {...fadeUp(0.05)}>
          <p className="text-[11px] font-semibold text-brand-teal uppercase tracking-[0.12em] mb-2">How It Works</p>
          <h2 className="font-display font-bold text-[22px] text-ink-rich tracking-tight mb-6">
            Three steps to better health
          </h2>
        </motion.div>

        <div className="space-y-4">
          {STEPS.map((step, i) => (
            <motion.div
              key={step.num}
              {...fadeUp(0.1 + i * 0.08)}
              className="card p-5 relative overflow-hidden group"
            >
              {/* Step number watermark */}
              <span className="absolute top-3 right-4 font-display font-bold text-[48px] text-surface-border/60 leading-none select-none pointer-events-none">
                {step.num}
              </span>

              <div className="relative flex items-start gap-4">
                <div className={`w-11 h-11 rounded-2xl ${step.accent} flex items-center justify-center text-[20px] shrink-0 shadow-sm`}>
                  {step.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-display font-bold text-[15px] text-ink-rich mb-1">
                    {step.title}
                  </h3>
                  <p className="text-[13px] text-ink-secondary leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Services ── */}
      <section className="px-5 py-8">
        <motion.div {...fadeUp(0.05)}>
          <p className="text-[11px] font-semibold text-brand-teal uppercase tracking-[0.12em] mb-2">Services</p>
          <h2 className="font-display font-bold text-[22px] text-ink-rich tracking-tight mb-6">
            Care that fits your needs
          </h2>
        </motion.div>

        <div className="space-y-3">
          {SERVICES.map((svc, i) => {
            const inner = (
              <div className={`card p-5 ${svc.href ? "card-interactive" : ""}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-surface-muted flex items-center justify-center text-[20px]">
                    {svc.icon}
                  </div>
                  <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg ${svc.tagColor}`}>
                    {svc.tag}
                  </span>
                </div>
                <h3 className="font-display font-bold text-[15px] text-ink-rich mb-1">{svc.title}</h3>
                <p className="text-[13px] text-ink-secondary leading-relaxed">{svc.desc}</p>
              </div>
            );

            return (
              <motion.div key={svc.title} {...fadeUp(0.1 + i * 0.06)}>
                {svc.href ? <Link href={svc.href}>{inner}</Link> : inner}
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ── Packages ── */}
      <section className="px-5 py-8">
        <motion.div {...fadeUp(0.05)}>
          <p className="text-[11px] font-semibold text-brand-teal uppercase tracking-[0.12em] mb-2">Packages</p>
          <h2 className="font-display font-bold text-[22px] text-ink-rich tracking-tight mb-6">
            Start free, upgrade anytime
          </h2>
        </motion.div>

        <div className="space-y-3">
          {/* Free Trial */}
          <motion.div {...fadeUp(0.1)}>
            <Link href="/book">
              <div className="card card-interactive p-5 border-l-4 border-l-emerald-400">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-display font-bold text-[16px] text-ink-rich">Free Trial</h3>
                  <span className="font-display font-bold text-[18px] text-emerald-600">FREE</span>
                </div>
                <p className="text-[13px] text-ink-secondary leading-relaxed mb-3">
                  Try a 15-minute session with any available doctor. No payment needed — just book and talk.
                </p>
                <div className="flex items-center gap-4 text-[12px] text-ink-muted">
                  <span className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2"/><path d="M7 4v3.5l2.5 1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>
                    15 minutes
                  </span>
                  <span className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 7L5.5 10L11.5 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    One-time trial
                  </span>
                </div>
              </div>
            </Link>
          </motion.div>

          {/* Single Session */}
          <motion.div {...fadeUp(0.16)}>
            <Link href="/book">
              <div className="card card-interactive p-5 border-l-4 border-l-brand-teal relative overflow-hidden">
                {/* Popular badge */}
                <div className="absolute top-0 right-0 bg-brand-teal text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl">
                  POPULAR
                </div>

                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-display font-bold text-[16px] text-ink-rich">Single Session</h3>
                  <span className="font-display font-bold text-[18px] text-brand-teal-deep">500 ETB</span>
                </div>
                <p className="text-[13px] text-ink-secondary leading-relaxed mb-3">
                  Full 30-minute consultation with your chosen doctor. Follow-up included until your issue is resolved.
                </p>
                <div className="flex items-center gap-4 text-[12px] text-ink-muted">
                  <span className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2"/><path d="M7 4v3.5l2.5 1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>
                    30 minutes
                  </span>
                  <span className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 7L5.5 10L11.5 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    Follow-up included
                  </span>
                </div>
              </div>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Call Center ── */}
      <section className="px-5 py-6">
        <motion.div {...fadeUp(0.05)}>
          <div className="card p-5 bg-gradient-to-br from-surface-white to-brand-teal-light/30 text-center">
            <div className="w-12 h-12 rounded-2xl bg-brand-teal/10 flex items-center justify-center text-[24px] mx-auto mb-3">
              📞
            </div>
            <h3 className="font-display font-bold text-[16px] text-ink-rich mb-1">Need to talk now?</h3>
            <p className="text-[13px] text-ink-secondary mb-4">
              Our call center is available for urgent medical guidance.
            </p>
            <a
              href="tel:+251944140404"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-teal text-white font-display font-bold text-[14px] shadow-glow-sm active:scale-[0.97] transition-transform"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M6.5 3.5C6.5 3.5 6 2 4.5 2S2 3.5 2 5c0 3 4.5 8.5 4.5 8.5S8 12 9.5 11s2-2.5 2-2.5L9 6.5 6.5 3.5z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              +251 944 140 404
            </a>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <section className="px-5 pt-4 pb-2">
        <motion.div {...fadeUp(0.05)} className="text-center">
          <p className="text-[11px] text-ink-muted">
            All doctors are licensed and verified by LongiMed.
          </p>
          <p className="text-[10px] text-ink-faint mt-1">
            LongiMed Health Services PLC
          </p>
        </motion.div>
      </section>
    </div>
  );
}
