"use client";

import { useRef, useState, useEffect } from "react";
import Image from "next/image";
import { motion, useInView, useScroll, useTransform } from "framer-motion";
import type { Doctor } from "@/lib/api";

/* ── Scroll-triggered reveal ── */
function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.9, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

const BOT_LINK = "https://t.me/LongiMedBot";
const CALL = "+251 944 140 404";

const LANG_LABELS: Record<string, string> = { en: "English", am: "Amharic", or: "Oromifa", ti: "Tigrinya" };
const SPEC_LABELS: Record<string, string> = {
  general: "General Practice", family_medicine: "Family Medicine", internal_medicine: "Internal Medicine",
  pediatrics: "Pediatrics", obgyn: "OB/GYN", surgery: "Surgery", orthopedics: "Orthopedics",
  dermatology: "Dermatology", mental_health: "Mental Health", cardiology: "Cardiology",
  neurology: "Neurology", ent: "ENT", ophthalmology: "Ophthalmology", other: "Specialist",
};

export default function LandingPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);

  useEffect(() => {
    fetch("/api/doctors")
      .then((r) => r.ok ? r.json() : [])
      .then((data: Doctor[]) => {
        const real = data
          .filter((d) =>
            d.is_available &&
            d.full_name &&
            d.full_name.length > 5 &&
            !/^(test|yest|demo)\b/i.test(d.full_name)
          )
          .sort((a, b) => {
            const score = (d: Doctor) =>
              (d.profile_photo_url ? 4 : 0) +
              (d.bio && d.bio.length >= 30 ? 2 : 0) +
              (d.rating_avg > 0 ? 1 : 0);
            return score(b) - score(a);
          });
        setDoctors(real.slice(0, 4));
      })
      .catch(() => {});
  }, []);

  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const parallaxY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const fadeOut = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto overflow-x-hidden lm-landing">
      {/* ── Font injection ── */}
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;0,9..144,800;1,9..144,400;1,9..144,500&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

        .lm-landing {
          --cream: #FFFBF7;
          --cream-deep: #FFF3E8;
          --ivory: #FEFCF9;
          --terra: #D4725C;
          --terra-light: #F5E1DA;
          --terra-deep: #B85A46;
          --teal: #35C8BB;
          --teal-soft: #E8F8F6;
          --navy: #1A2540;
          --navy-60: #1A254099;
          --warm-gray: #6B6560;
          --warm-border: #EDE8E3;
          --warm-shadow: rgba(26, 37, 64, 0.06);

          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          background: var(--cream);
          color: var(--navy);
          -webkit-font-smoothing: antialiased;
        }
        .lm-landing .font-editorial {
          font-family: 'Fraunces', Georgia, serif;
        }

        /* Subtle grain overlay */
        .lm-landing::before {
          content: "";
          position: fixed;
          inset: 0;
          opacity: 0.025;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
          pointer-events: none;
          z-index: 1;
        }

        /* Meskel cross — very subtle on cream */
        .lm-meskel::after {
          content: "";
          position: absolute;
          inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg width='64' height='64' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M32 16v10h-10v10h10v12h10V36h10V26H42V16H32z' fill='none' stroke='%2335C8BB' stroke-width='0.5' opacity='0.06'/%3E%3C/svg%3E");
          pointer-events: none;
        }

        .lm-landing .doctor-card {
          transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        }
        .lm-landing .doctor-card:hover {
          transform: translateY(-6px);
          box-shadow: 0 20px 60px rgba(26, 37, 64, 0.1), 0 2px 8px rgba(26, 37, 64, 0.04);
        }

        .lm-landing .cta-glow {
          position: relative;
          overflow: hidden;
        }
        .lm-landing .cta-glow::after {
          content: "";
          position: absolute;
          inset: -1px;
          border-radius: inherit;
          background: linear-gradient(135deg, rgba(53,200,187,0.15), rgba(212,114,92,0.1));
          z-index: -1;
          filter: blur(12px);
          opacity: 0;
          transition: opacity 0.4s;
        }
        .lm-landing .cta-glow:hover::after {
          opacity: 1;
        }

        @keyframes float-slow {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-12px); }
        }
        @keyframes float-slower {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
      `}</style>

      {/* ═══════════════════════════════════════════
          NAVIGATION
      ═══════════════════════════════════════════ */}
      <nav className="sticky top-0 z-50 backdrop-blur-2xl border-b" style={{ background: 'rgba(255,251,247,0.85)', borderColor: 'var(--warm-border)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10 h-[72px] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image src="/logo-icon.png" alt="LongiMed" width={36} height={36} className="rounded-xl" />
            <span className="font-editorial text-[20px] font-semibold tracking-tight" style={{ color: 'var(--navy)' }}>
              LongiMed
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <a href="#how" className="text-[14px] font-medium hover:opacity-70 transition-opacity" style={{ color: 'var(--warm-gray)' }}>How it works</a>
            <a href="#doctors" className="text-[14px] font-medium hover:opacity-70 transition-opacity" style={{ color: 'var(--warm-gray)' }}>Our doctors</a>
            <a href="#articles" className="text-[14px] font-medium hover:opacity-70 transition-opacity" style={{ color: 'var(--warm-gray)' }}>Articles</a>
            <a href="#pricing" className="text-[14px] font-medium hover:opacity-70 transition-opacity" style={{ color: 'var(--warm-gray)' }}>Pricing</a>
            <a href={`tel:${CALL.replace(/\s/g, "")}`} className="text-[14px] font-medium flex items-center gap-1.5 hover:opacity-70 transition-opacity" style={{ color: 'var(--warm-gray)' }}>
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
              {CALL}
            </a>
          </div>

          <a
            href={BOT_LINK}
            target="_blank"
            rel="noopener noreferrer"
            className="cta-glow inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-semibold text-[13px] text-white transition-all active:scale-[0.97]"
            style={{ background: 'var(--teal)' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.14.14 0 00-.07-.2c-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.66-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.88 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.45 0 .06.01.24 0 .37z"/></svg>
            Start Free
          </a>
        </div>
      </nav>

      {/* ═══════════════════════════════════════════
          HERO
      ═══════════════════════════════════════════ */}
      <section ref={heroRef} className="relative overflow-hidden lm-meskel" style={{ background: 'var(--cream)' }}>
        {/* Warm gradient orbs */}
        <div className="absolute top-[-15%] right-[-8%] w-[600px] h-[600px] rounded-full pointer-events-none" style={{ background: 'radial-gradient(circle, rgba(212,114,92,0.08) 0%, transparent 70%)' }} />
        <div className="absolute bottom-[-20%] left-[-12%] w-[500px] h-[500px] rounded-full pointer-events-none" style={{ background: 'radial-gradient(circle, rgba(53,200,187,0.06) 0%, transparent 70%)' }} />

        <motion.div
          style={{ y: parallaxY, opacity: fadeOut }}
          className="relative max-w-7xl mx-auto px-6 sm:px-10 pt-20 sm:pt-28 lg:pt-36 pb-24 sm:pb-32"
        >
          <div className="grid lg:grid-cols-[1fr_auto] gap-16 lg:gap-24 items-center">
            {/* Copy */}
            <div className="max-w-2xl">
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              >
                <span
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-[12px] font-semibold tracking-wide uppercase mb-8"
                  style={{ background: 'var(--teal-soft)', color: 'var(--teal)' }}
                >
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#22C55E' }} />
                  Doctors online now
                </span>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.9, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
                className="font-editorial font-medium text-[44px] sm:text-[56px] lg:text-[68px] leading-[1.05] tracking-[-0.03em] mb-6"
                style={{ color: 'var(--navy)' }}
              >
                Healthcare
                <br />
                that comes{" "}
                <span className="italic" style={{ color: 'var(--terra)' }}>
                  to you
                </span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
                className="text-[18px] sm:text-[20px] leading-[1.6] max-w-[520px] mb-10"
                style={{ color: 'var(--warm-gray)' }}
              >
                Connect with verified Ethiopian physicians through Telegram.
                Ask for free, or book a private consultation — all from where you are.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.9, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
                className="flex flex-col sm:flex-row gap-4"
              >
                <a
                  href={BOT_LINK}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group cta-glow inline-flex items-center justify-center gap-3 px-8 py-4 rounded-full text-white font-semibold text-[15px] active:scale-[0.97] transition-transform"
                  style={{ background: 'var(--navy)' }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" className="group-hover:scale-110 transition-transform"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.14.14 0 00-.07-.2c-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.66-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.88 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.45 0 .06.01.24 0 .37z"/></svg>
                  Open on Telegram
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="group-hover:translate-x-1 transition-transform"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                </a>
                <a
                  href={`tel:${CALL.replace(/\s/g, "")}`}
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full font-semibold text-[15px] border transition-colors active:scale-[0.97]"
                  style={{ borderColor: 'var(--warm-border)', color: 'var(--navy)' }}
                >
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                  Call us
                </a>
              </motion.div>
            </div>

            {/* Hero visual — single photo */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.2, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
              className="hidden lg:block relative"
            >
              <div
                className="w-[340px] h-[420px] rounded-[36px] overflow-hidden relative"
                style={{ boxShadow: '0 32px 80px rgba(26,37,64,0.12), 0 2px 4px rgba(26,37,64,0.04)' }}
              >
                <img src="/photos/hero_nurse.png" alt="Ethiopian healthcare professional" className="w-full h-full object-cover" />
                {/* Subtle gradient overlay at bottom */}
                <div className="absolute inset-x-0 bottom-0 h-1/3" style={{ background: 'linear-gradient(to top, rgba(26,37,64,0.4), transparent)' }} />
              </div>
              {/* Floating badge */}
              <div
                className="absolute -bottom-4 -left-6 z-20 px-5 py-3 rounded-2xl flex items-center gap-2.5"
                style={{
                  background: '#FFFFFF',
                  boxShadow: '0 8px 32px rgba(26,37,64,0.1)',
                  animation: 'float-slow 5s ease-in-out infinite',
                }}
              >
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#22C55E' }} />
                <span className="text-[13px] font-semibold" style={{ color: 'var(--navy)' }}>Doctors Online Now</span>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          TRUST BAR
      ═══════════════════════════════════════════ */}
      <Reveal>
        <div className="border-y py-6 sm:py-8" style={{ borderColor: 'var(--warm-border)', background: 'var(--ivory)' }}>
          <div className="max-w-7xl mx-auto px-6 sm:px-10 flex flex-wrap items-center justify-center gap-x-10 gap-y-3 text-[13px] sm:text-[14px] font-medium" style={{ color: 'var(--warm-gray)' }}>
            {[
              { icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>, text: "Licensed Physicians" },
              { icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364V3" /></svg>, text: "Amharic & English" },
              { icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>, text: "24 / 7 Available" },
              { icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" /></svg>, text: "Anonymous Option" },
            ].map((item) => (
              <span key={item.text} className="inline-flex items-center gap-2">
                <span style={{ color: 'var(--teal)' }}>{item.icon}</span>
                {item.text}
              </span>
            ))}
          </div>
        </div>
      </Reveal>

      {/* ═══════════════════════════════════════════
          HOW IT WORKS
      ═══════════════════════════════════════════ */}
      <section id="how" className="relative py-24 sm:py-32" style={{ background: 'var(--cream)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10">
          <Reveal className="mb-16 sm:mb-20">
            <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-4" style={{ color: 'var(--terra)' }}>
              How it works
            </p>
            <h2 className="font-editorial font-medium text-[32px] sm:text-[44px] leading-[1.1] tracking-[-0.02em]" style={{ color: 'var(--navy)' }}>
              Three simple steps
            </h2>
          </Reveal>

          <div className="grid sm:grid-cols-3 gap-8 sm:gap-12 relative">
            {/* Connecting line — desktop only */}
            <div className="hidden sm:block absolute top-[44px] left-[16%] right-[16%] h-px" style={{ background: 'var(--warm-border)' }} />

            {[
              {
                num: "01",
                title: "Open the bot",
                desc: "Tap the button to start LongiMed on Telegram. No app download — just open and chat.",
                icon: <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" /></svg>,
              },
              {
                num: "02",
                title: "Describe your concern",
                desc: "Tell us what you need. We match you with the right specialist or post to our free Q&A.",
                icon: <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>,
              },
              {
                num: "03",
                title: "Get your answers",
                desc: "Consult privately via text or voice. Secure, anonymous if you choose, fully confidential.",
                icon: <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" /></svg>,
              },
            ].map((step, i) => (
              <Reveal key={step.num} delay={i * 0.12}>
                <div className="text-center relative">
                  {/* Number circle */}
                  <div
                    className="w-[88px] h-[88px] rounded-full mx-auto mb-6 flex items-center justify-center relative z-10"
                    style={{
                      background: i === 0 ? 'var(--navy)' : 'var(--ivory)',
                      border: i === 0 ? 'none' : '1.5px solid var(--warm-border)',
                      color: i === 0 ? '#fff' : 'var(--navy)',
                    }}
                  >
                    {step.icon}
                  </div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.2em] mb-2" style={{ color: 'var(--terra)' }}>
                    Step {step.num}
                  </p>
                  <h3 className="font-editorial font-medium text-[20px] sm:text-[22px] mb-3" style={{ color: 'var(--navy)' }}>
                    {step.title}
                  </h3>
                  <p className="text-[15px] leading-[1.7] max-w-[300px] mx-auto" style={{ color: 'var(--warm-gray)' }}>
                    {step.desc}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          CONSULTATION PHOTO BREAK
      ═══════════════════════════════════════════ */}
      <Reveal>
        <div className="max-w-7xl mx-auto px-6 sm:px-10 py-8">
          <div
            className="relative rounded-[28px] overflow-hidden h-[280px] sm:h-[360px]"
            style={{ boxShadow: '0 16px 48px rgba(26,37,64,0.08)' }}
          >
            <img
              src="/photos/consultation.png"
              alt="Doctor consulting with patient"
              className="w-full h-full object-cover"
            />
            <div
              className="absolute inset-0"
              style={{ background: 'linear-gradient(to right, var(--navy) 0%, rgba(26,37,64,0.3) 60%, transparent 100%)' }}
            />
            <div className="absolute inset-0 flex items-center px-10 sm:px-16">
              <div>
                <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-3" style={{ color: 'var(--teal)' }}>
                  Private & Confidential
                </p>
                <h3 className="font-editorial font-medium text-[24px] sm:text-[36px] text-white leading-[1.15] tracking-[-0.02em] max-w-md">
                  Real doctors.
                  <br />
                  Real <span className="italic" style={{ color: 'var(--teal)' }}>conversations</span>.
                </h3>
              </div>
            </div>
          </div>
        </div>
      </Reveal>

      {/* ═══════════════════════════════════════════
          MEET OUR DOCTORS
      ═══════════════════════════════════════════ */}
      <section id="doctors" className="relative py-24 sm:py-32 overflow-hidden" style={{ background: 'var(--ivory)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10">
          <Reveal className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-14">
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-4" style={{ color: 'var(--terra)' }}>
                Our doctors
              </p>
              <h2 className="font-editorial font-medium text-[32px] sm:text-[44px] leading-[1.1] tracking-[-0.02em]" style={{ color: 'var(--navy)' }}>
                Meet who&rsquo;s{" "}
                <span className="italic" style={{ color: 'var(--terra)' }}>caring</span>
                {" "}for you
              </h2>
            </div>
            <a
              href={BOT_LINK}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[14px] font-semibold inline-flex items-center gap-1.5 hover:gap-2.5 transition-all"
              style={{ color: 'var(--teal)' }}
            >
              View all doctors
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
            </a>
          </Reveal>

          {doctors.length === 0 ? (
            /* Skeleton while loading */
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="rounded-[20px] p-6 animate-pulse" style={{ background: '#FFFFFF', border: '1px solid var(--warm-border)' }}>
                  <div className="w-[72px] h-[72px] rounded-full mb-5" style={{ background: 'var(--cream-deep)' }} />
                  <div className="h-5 rounded w-3/4 mb-2" style={{ background: 'var(--cream-deep)' }} />
                  <div className="h-4 rounded w-1/2 mb-3" style={{ background: 'var(--cream-deep)' }} />
                  <div className="h-3 rounded w-full mb-2" style={{ background: 'var(--cream-deep)' }} />
                  <div className="h-3 rounded w-2/3" style={{ background: 'var(--cream-deep)' }} />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {doctors.map((doc, i) => {
                const initials = doc.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2);
                const specLabel = SPEC_LABELS[(doc.specialties || [doc.specialty])[0]] || doc.specialty;
                return (
                  <Reveal key={doc.id} delay={i * 0.1}>
                    <div
                      className="doctor-card rounded-[20px] p-6 relative overflow-hidden"
                      style={{
                        background: '#FFFFFF',
                        border: '1px solid var(--warm-border)',
                        boxShadow: '0 4px 24px var(--warm-shadow)',
                      }}
                    >
                      {/* Availability badge */}
                      {doc.is_available && (
                        <div className="absolute top-4 right-4 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold" style={{ background: '#ECFDF5', color: '#059669' }}>
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                          Online
                        </div>
                      )}

                      {/* Photo or initials */}
                      <div className="mb-5">
                        {doc.profile_photo_url ? (
                          <div className="w-[72px] h-[72px] rounded-full overflow-hidden" style={{ border: '3px solid var(--cream-deep)' }}>
                            <img
                              src={doc.profile_photo_url}
                              alt={doc.full_name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        ) : (
                          <div
                            className="w-[72px] h-[72px] rounded-full flex items-center justify-center font-editorial font-medium text-[22px]"
                            style={{
                              background: i % 2 === 0 ? 'var(--teal-soft)' : 'var(--terra-light)',
                              color: i % 2 === 0 ? 'var(--teal)' : 'var(--terra)',
                              border: `3px solid ${i % 2 === 0 ? 'rgba(53,200,187,0.15)' : 'rgba(212,114,92,0.15)'}`,
                            }}
                          >
                            {initials}
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <h3 className="font-editorial font-medium text-[17px] mb-1" style={{ color: 'var(--navy)' }}>
                        Dr. {doc.full_name}
                      </h3>
                      <p className="text-[13px] font-medium mb-2" style={{ color: 'var(--teal)' }}>
                        {specLabel}
                      </p>
                      {doc.bio && (
                        <p className="text-[13px] leading-[1.6] mb-4" style={{ color: 'var(--warm-gray)' }}>
                          {doc.bio.length > 80 ? doc.bio.slice(0, 80) + "..." : doc.bio}
                        </p>
                      )}

                      {/* Languages + rating */}
                      <div className="flex flex-wrap gap-1.5">
                        {doc.languages.map((lang) => (
                          <span
                            key={lang}
                            className="text-[11px] font-medium px-2.5 py-1 rounded-full"
                            style={{ background: 'var(--cream)', color: 'var(--warm-gray)' }}
                          >
                            {LANG_LABELS[lang] || lang}
                          </span>
                        ))}
                        {doc.rating_avg > 0 && (
                          <span
                            className="text-[11px] font-semibold px-2.5 py-1 rounded-full flex items-center gap-1"
                            style={{ background: '#FFF8E1', color: '#B8860B' }}
                          >
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
                            {doc.rating_avg}
                          </span>
                        )}
                      </div>
                    </div>
                  </Reveal>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SERVICES — editorial layout
      ═══════════════════════════════════════════ */}
      <section className="relative py-24 sm:py-32" style={{ background: 'var(--cream)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10">
          <Reveal className="mb-16">
            <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-4" style={{ color: 'var(--terra)' }}>
              What we offer
            </p>
            <h2 className="font-editorial font-medium text-[32px] sm:text-[44px] leading-[1.1] tracking-[-0.02em] max-w-lg" style={{ color: 'var(--navy)' }}>
              Care designed around{" "}
              <span className="italic" style={{ color: 'var(--terra)' }}>your life</span>
            </h2>
          </Reveal>

          <div className="space-y-8">
            {[
              {
                title: "Free Q & A",
                desc: "Post your health question — anonymously if you prefer. Verified doctors answer publicly, helping you and the community. No cost, no commitment.",
                tag: "Free",
                tagBg: "#ECFDF5",
                tagColor: "#059669",
                accent: "var(--teal)",
                icon: <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" /></svg>,
              },
              {
                title: "Private Consultation",
                desc: "One-on-one with your chosen specialist. Share text, voice notes, and images in a fully confidential session. Stay anonymous if you need to.",
                tag: "From 500 ETB",
                tagBg: "var(--teal-soft)",
                tagColor: "var(--teal)",
                accent: "var(--navy)",
                icon: <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>,
              },
              {
                title: "Emergency Line",
                desc: "Our bot detects emergencies the moment you type. Instant routing to 907, 991, or 939 plus a map to the nearest hospital. No delay, no menus.",
                tag: "24 / 7",
                tagBg: "#FEF2F2",
                tagColor: "#DC2626",
                accent: "var(--terra)",
                icon: <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>,
              },
            ].map((svc, i) => (
              <Reveal key={svc.title} delay={i * 0.1}>
                <div
                  className="rounded-[20px] p-8 sm:p-10 flex flex-col sm:flex-row sm:items-start gap-6 sm:gap-10 transition-all"
                  style={{
                    background: '#FFFFFF',
                    border: '1px solid var(--warm-border)',
                    boxShadow: '0 2px 16px var(--warm-shadow)',
                  }}
                >
                  {/* Icon */}
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center shrink-0"
                    style={{ background: 'var(--cream)', color: svc.accent }}
                  >
                    {svc.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-3 mb-3">
                      <h3 className="font-editorial font-medium text-[22px]" style={{ color: 'var(--navy)' }}>
                        {svc.title}
                      </h3>
                      <span
                        className="text-[11px] font-bold px-3 py-1 rounded-full"
                        style={{ background: svc.tagBg, color: svc.tagColor }}
                      >
                        {svc.tag}
                      </span>
                    </div>
                    <p className="text-[15px] sm:text-[16px] leading-[1.7] max-w-2xl" style={{ color: 'var(--warm-gray)' }}>
                      {svc.desc}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          ARTICLES — editorial reading list
      ═══════════════════════════════════════════ */}
      <section id="articles" className="relative py-24 sm:py-32" style={{ background: 'var(--cream)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10">
          <Reveal className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-14">
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-4" style={{ color: 'var(--terra)' }}>
                From our doctors
              </p>
              <h2 className="font-editorial font-medium text-[32px] sm:text-[44px] leading-[1.1] tracking-[-0.02em] max-w-xl" style={{ color: 'var(--navy)' }}>
                Notes on health,{" "}
                <span className="italic" style={{ color: 'var(--terra)' }}>written for you</span>
              </h2>
            </div>
            <a
              href="/articles"
              className="text-[14px] font-semibold inline-flex items-center gap-1.5 hover:gap-2.5 transition-all"
              style={{ color: 'var(--teal)' }}
            >
              Read all articles
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
            </a>
          </Reveal>

          <div className="grid md:grid-cols-3 gap-6 sm:gap-8">
            {[
              {
                category: "Maternal health",
                date: "Coming soon",
                read: "6 min read",
                title: "What every Ethiopian mother should know in the first trimester",
                excerpt: "Iron, folate, and the conversations worth having with your doctor before week twelve.",
                accent: "var(--terra)",
              },
              {
                category: "Mental health",
                date: "Coming soon",
                read: "8 min read",
                title: "Anxiety isn't weakness — and it isn't rare here either",
                excerpt: "Why so many of us carry it quietly, and the small first steps that actually help.",
                accent: "var(--teal)",
              },
              {
                category: "Chronic care",
                date: "Coming soon",
                read: "5 min read",
                title: "Living well with hypertension on an Addis schedule",
                excerpt: "Practical food, movement, and medication rhythms that fit a real Ethiopian week.",
                accent: "var(--navy)",
              },
            ].map((article, i) => (
              <Reveal key={article.title} delay={i * 0.1}>
                <a
                  href="/articles"
                  className="doctor-card block rounded-[20px] overflow-hidden h-full"
                  style={{
                    background: '#FFFFFF',
                    border: '1px solid var(--warm-border)',
                    boxShadow: '0 2px 16px var(--warm-shadow)',
                  }}
                >
                  {/* Cover band — colored gradient with floating glyph */}
                  <div
                    className="relative h-[160px] overflow-hidden"
                    style={{
                      background: `linear-gradient(135deg, ${article.accent} 0%, var(--navy) 140%)`,
                    }}
                  >
                    <div className="absolute inset-0 opacity-[0.08]" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20 8v8h-8v8h8v8h8v-8h8v-8h-8V8z' fill='none' stroke='%23ffffff' stroke-width='0.6'/%3E%3C/svg%3E')" }} />
                    <div className="absolute bottom-5 left-6">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-[11px] font-semibold uppercase tracking-[0.15em] backdrop-blur" style={{ background: 'rgba(255,255,255,0.15)', color: '#FFFFFF' }}>
                        {article.category}
                      </span>
                    </div>
                  </div>

                  {/* Body */}
                  <div className="p-6 sm:p-7">
                    <div className="flex items-center gap-3 text-[12px] mb-3" style={{ color: 'var(--warm-gray)' }}>
                      <span>{article.date}</span>
                      <span className="w-1 h-1 rounded-full" style={{ background: 'var(--warm-border)' }} />
                      <span>{article.read}</span>
                    </div>
                    <h3 className="font-editorial font-medium text-[20px] sm:text-[22px] leading-[1.3] mb-3 tracking-[-0.01em]" style={{ color: 'var(--navy)' }}>
                      {article.title}
                    </h3>
                    <p className="text-[14px] leading-[1.65] mb-5" style={{ color: 'var(--warm-gray)' }}>
                      {article.excerpt}
                    </p>
                    <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold" style={{ color: article.accent }}>
                      Read article
                      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                    </span>
                  </div>
                </a>
              </Reveal>
            ))}
          </div>

          {/* Newsletter strip */}
          <Reveal delay={0.2}>
            <div
              className="mt-16 rounded-[24px] p-8 sm:p-10 flex flex-col sm:flex-row sm:items-center justify-between gap-6"
              style={{
                background: 'var(--ivory)',
                border: '1px solid var(--warm-border)',
              }}
            >
              <div className="max-w-md">
                <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-2" style={{ color: 'var(--terra)' }}>
                  Stay in the loop
                </p>
                <h3 className="font-editorial font-medium text-[20px] sm:text-[24px] leading-[1.2]" style={{ color: 'var(--navy)' }}>
                  New articles, straight to Telegram.
                </h3>
              </div>
              <a
                href={BOT_LINK}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full font-semibold text-[14px] text-white whitespace-nowrap active:scale-[0.97] transition-transform"
                style={{ background: 'var(--navy)' }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.14.14 0 00-.07-.2c-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.66-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.88 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.45 0 .06.01.24 0 .37z"/></svg>
                Follow on Telegram
              </a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          PRICING
      ═══════════════════════════════════════════ */}
      <section id="pricing" className="relative py-24 sm:py-32" style={{ background: 'var(--ivory)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10">
          <Reveal className="text-center mb-14">
            <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-4" style={{ color: 'var(--terra)' }}>
              Simple pricing
            </p>
            <h2 className="font-editorial font-medium text-[32px] sm:text-[44px] leading-[1.1] tracking-[-0.02em]" style={{ color: 'var(--navy)' }}>
              Transparent. Affordable.
            </h2>
            <p className="text-[16px] mt-4 max-w-md mx-auto" style={{ color: 'var(--warm-gray)' }}>
              Start free — upgrade only when you need more time.
            </p>
          </Reveal>

          <div className="grid sm:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Free */}
            <Reveal>
              <div
                className="rounded-[20px] p-8 h-full flex flex-col"
                style={{
                  background: '#FFFFFF',
                  border: '1px solid var(--warm-border)',
                  boxShadow: '0 2px 16px var(--warm-shadow)',
                }}
              >
                <p className="text-[12px] font-semibold uppercase tracking-[0.15em] mb-6" style={{ color: 'var(--warm-gray)' }}>
                  Free trial
                </p>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="font-editorial font-medium text-[48px] leading-none" style={{ color: 'var(--navy)' }}>0</span>
                  <span className="text-[16px] font-medium" style={{ color: 'var(--warm-gray)' }}>ETB</span>
                </div>
                <p className="text-[14px] mb-8" style={{ color: 'var(--warm-gray)' }}>15-minute consultation</p>

                <ul className="space-y-3 flex-1 mb-8">
                  {["One-time per account", "Any available doctor", "Full chat features", "Amharic or English"].map((f) => (
                    <li key={f} className="flex items-start gap-3 text-[14px]" style={{ color: 'var(--navy)' }}>
                      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" className="shrink-0 mt-0.5" style={{ color: 'var(--teal)' }}><path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                      {f}
                    </li>
                  ))}
                </ul>

                <a
                  href={BOT_LINK}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-center py-3.5 rounded-full font-semibold text-[14px] border-2 transition-colors active:scale-[0.97]"
                  style={{ borderColor: 'var(--warm-border)', color: 'var(--navy)' }}
                >
                  Try free
                </a>
              </div>
            </Reveal>

            {/* Paid */}
            <Reveal delay={0.1}>
              <div
                className="rounded-[20px] p-8 h-full flex flex-col relative overflow-hidden"
                style={{
                  background: '#FFFFFF',
                  border: '1.5px solid var(--teal)',
                  boxShadow: '0 4px 32px rgba(53,200,187,0.1), 0 2px 16px var(--warm-shadow)',
                }}
              >
                {/* Recommended tag */}
                <div
                  className="absolute top-0 right-6 px-3 py-1.5 rounded-b-lg text-[10px] font-bold uppercase tracking-wide text-white"
                  style={{ background: 'var(--teal)' }}
                >
                  Popular
                </div>

                <p className="text-[12px] font-semibold uppercase tracking-[0.15em] mb-6" style={{ color: 'var(--warm-gray)' }}>
                  Single session
                </p>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="font-editorial font-medium text-[48px] leading-none" style={{ color: 'var(--navy)' }}>500</span>
                  <span className="text-[16px] font-medium" style={{ color: 'var(--warm-gray)' }}>ETB</span>
                </div>
                <p className="text-[14px] mb-8" style={{ color: 'var(--warm-gray)' }}>30-minute consultation</p>

                <ul className="space-y-3 flex-1 mb-8">
                  {["Choose your specialist", "Follow-up included", "Anonymous option", "Voice notes & images", "Priority matching"].map((f) => (
                    <li key={f} className="flex items-start gap-3 text-[14px]" style={{ color: 'var(--navy)' }}>
                      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" className="shrink-0 mt-0.5" style={{ color: 'var(--teal)' }}><path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                      {f}
                    </li>
                  ))}
                </ul>

                <a
                  href={BOT_LINK}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cta-glow block text-center py-3.5 rounded-full font-semibold text-[14px] text-white active:scale-[0.97] transition-transform"
                  style={{ background: 'var(--teal)' }}
                >
                  Book a session
                </a>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FINAL CTA
      ═══════════════════════════════════════════ */}
      <section className="relative py-24 sm:py-32" style={{ background: 'var(--cream)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10">
          <Reveal>
            <div
              className="relative rounded-[28px] sm:rounded-[36px] overflow-hidden px-8 sm:px-16 py-16 sm:py-20 text-center"
              style={{
                background: 'var(--navy)',
              }}
            >
              {/* Decorative elements */}
              <div className="absolute top-[-60px] right-[-40px] w-[280px] h-[280px] rounded-full" style={{ background: 'rgba(53,200,187,0.08)' }} />
              <div className="absolute bottom-[-80px] left-[-50px] w-[320px] h-[320px] rounded-full" style={{ background: 'rgba(212,114,92,0.06)' }} />
              <div className="absolute top-8 left-8 w-2 h-2 rounded-full" style={{ background: 'var(--teal)', opacity: 0.3 }} />
              <div className="absolute bottom-12 right-16 w-3 h-3 rounded-full" style={{ background: 'var(--terra)', opacity: 0.2 }} />

              <div className="relative">
                <h2 className="font-editorial font-medium text-[28px] sm:text-[44px] text-white leading-[1.1] tracking-[-0.02em] mb-5">
                  Your doctor is one
                  <br />
                  <span className="italic" style={{ color: 'var(--teal)' }}>message</span> away
                </h2>
                <p className="text-[16px] sm:text-[18px] leading-[1.6] max-w-md mx-auto mb-10" style={{ color: 'rgba(255,255,255,0.6)' }}>
                  Open LongiMed on Telegram and start your free consultation. No downloads, no waiting rooms.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <a
                    href={BOT_LINK}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group inline-flex items-center justify-center gap-3 px-8 py-4 rounded-full text-[15px] font-semibold transition-all active:scale-[0.97]"
                    style={{ background: '#FFFFFF', color: 'var(--navy)' }}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--teal)"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.14.14 0 00-.07-.2c-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.66-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.88 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.45 0 .06.01.24 0 .37z"/></svg>
                    Open LongiMed Bot
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="group-hover:translate-x-1 transition-transform"><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                  </a>
                  <a
                    href={`tel:${CALL.replace(/\s/g, "")}`}
                    className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full text-[15px] font-semibold border transition-colors active:scale-[0.97]"
                    style={{ borderColor: 'rgba(255,255,255,0.15)', color: 'rgba(255,255,255,0.8)' }}
                  >
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                    {CALL}
                  </a>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════ */}
      <footer className="border-t" style={{ borderColor: 'var(--warm-border)', background: 'var(--cream)' }}>
        <div className="max-w-7xl mx-auto px-6 sm:px-10 pt-16 pb-10">
          {/* Top grid */}
          <div className="grid grid-cols-2 md:grid-cols-12 gap-10 sm:gap-8 mb-12">
            {/* Brand block */}
            <div className="col-span-2 md:col-span-4">
              <div className="flex items-center gap-3 mb-5">
                <Image src="/logo-icon.png" alt="LongiMed" width={32} height={32} className="rounded-lg" />
                <span className="font-editorial font-semibold text-[20px] tracking-tight" style={{ color: 'var(--navy)' }}>
                  LongiMed
                </span>
              </div>
              <p className="text-[14px] leading-[1.65] max-w-[280px] mb-6" style={{ color: 'var(--warm-gray)' }}>
                Verified Ethiopian doctors on Telegram. Free Q&amp;A, private consultations, emergency guidance — wherever you are.
              </p>
              <div className="flex items-center gap-3">
                <a
                  href={BOT_LINK}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Telegram"
                  className="w-9 h-9 rounded-full flex items-center justify-center transition-colors"
                  style={{ background: 'var(--ivory)', border: '1px solid var(--warm-border)', color: 'var(--navy)' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.14.14 0 00-.07-.2c-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.66-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.88 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.45 0 .06.01.24 0 .37z"/></svg>
                </a>
                <a
                  href={`tel:${CALL.replace(/\s/g, "")}`}
                  aria-label="Call"
                  className="w-9 h-9 rounded-full flex items-center justify-center transition-colors"
                  style={{ background: 'var(--ivory)', border: '1px solid var(--warm-border)', color: 'var(--navy)' }}
                >
                  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                </a>
                <a
                  href="mailto:hello@longimed.com"
                  aria-label="Email"
                  className="w-9 h-9 rounded-full flex items-center justify-center transition-colors"
                  style={{ background: 'var(--ivory)', border: '1px solid var(--warm-border)', color: 'var(--navy)' }}
                >
                  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>
                </a>
              </div>
            </div>

            {/* Explore */}
            <div className="col-span-1 md:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] mb-4" style={{ color: 'var(--navy)' }}>
                Explore
              </p>
              <ul className="space-y-3 text-[13px]" style={{ color: 'var(--warm-gray)' }}>
                <li><a href="#how" className="hover:opacity-70 transition-opacity">How it works</a></li>
                <li><a href="#doctors" className="hover:opacity-70 transition-opacity">Our doctors</a></li>
                <li><a href="#articles" className="hover:opacity-70 transition-opacity">Articles</a></li>
                <li><a href="#pricing" className="hover:opacity-70 transition-opacity">Pricing</a></li>
              </ul>
            </div>

            {/* Services */}
            <div className="col-span-1 md:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] mb-4" style={{ color: 'var(--navy)' }}>
                Services
              </p>
              <ul className="space-y-3 text-[13px]" style={{ color: 'var(--warm-gray)' }}>
                <li><a href={BOT_LINK} target="_blank" rel="noopener noreferrer" className="hover:opacity-70 transition-opacity">Free Q&amp;A</a></li>
                <li><a href={BOT_LINK} target="_blank" rel="noopener noreferrer" className="hover:opacity-70 transition-opacity">Private consultation</a></li>
                <li><a href={BOT_LINK} target="_blank" rel="noopener noreferrer" className="hover:opacity-70 transition-opacity">Emergency line</a></li>
                <li><a href={BOT_LINK} target="_blank" rel="noopener noreferrer" className="hover:opacity-70 transition-opacity">Diaspora consults</a></li>
              </ul>
            </div>

            {/* For doctors */}
            <div className="col-span-1 md:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] mb-4" style={{ color: 'var(--navy)' }}>
                For doctors
              </p>
              <ul className="space-y-3 text-[13px]" style={{ color: 'var(--warm-gray)' }}>
                <li><a href={BOT_LINK} target="_blank" rel="noopener noreferrer" className="hover:opacity-70 transition-opacity">Join the platform</a></li>
                <li><a href={BOT_LINK} target="_blank" rel="noopener noreferrer" className="hover:opacity-70 transition-opacity">How payouts work</a></li>
                <li><a href="mailto:doctors@longimed.com" className="hover:opacity-70 transition-opacity">Partnership inquiries</a></li>
              </ul>
            </div>

            {/* Contact */}
            <div className="col-span-1 md:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] mb-4" style={{ color: 'var(--navy)' }}>
                Contact
              </p>
              <ul className="space-y-3 text-[13px]" style={{ color: 'var(--warm-gray)' }}>
                <li>
                  <a href={`tel:${CALL.replace(/\s/g, "")}`} className="hover:opacity-70 transition-opacity">
                    {CALL}
                  </a>
                </li>
                <li>
                  <a href="mailto:hello@longimed.com" className="hover:opacity-70 transition-opacity">
                    hello@longimed.com
                  </a>
                </li>
                <li>Addis Ababa, Ethiopia</li>
              </ul>
            </div>
          </div>

          {/* Bottom strip */}
          <div className="pt-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-t" style={{ borderColor: 'var(--warm-border)' }}>
            <p className="text-[11px]" style={{ color: 'var(--warm-gray)', opacity: 0.7 }}>
              &copy; 2026 LongiMed Health Services PLC. All rights reserved.
            </p>
            <div className="flex items-center gap-6 text-[11px]" style={{ color: 'var(--warm-gray)', opacity: 0.7 }}>
              <a href="/privacy" className="hover:opacity-100 transition-opacity">Privacy</a>
              <a href="/terms" className="hover:opacity-100 transition-opacity">Terms</a>
              <a href="/about" className="hover:opacity-100 transition-opacity">About</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
