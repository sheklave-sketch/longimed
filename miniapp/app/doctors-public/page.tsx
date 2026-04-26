"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import type { Doctor } from "@/lib/api";

const BOT_LINK = "https://t.me/longimed_bot";
const CALL = "+251 944 140 404";
const WA_DIGITS = CALL.replace(/\D/g, "");

const SPEC_LABELS: Record<string, string> = {
  general: "General Practice", family_medicine: "Family Medicine", internal_medicine: "Internal Medicine",
  pediatrics: "Pediatrics", obgyn: "OB/GYN", surgery: "Surgery", orthopedics: "Orthopedics",
  dermatology: "Dermatology", mental_health: "Mental Health", cardiology: "Cardiology",
  neurology: "Neurology", ent: "ENT", ophthalmology: "Ophthalmology", other: "Specialist",
};
const LANG_LABELS: Record<string, string> = { en: "English", am: "Amharic", or: "Oromifa", ti: "Tigrinya" };

const cleanName = (n: string) => n.replace(/^\s*(dr\.?\s+)+/i, "").trim();
const dedupKey = (n: string) => cleanName(n).toLowerCase().split(/\s+/).slice(0, 2).join(" ");

export default function PublicDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeSpec, setActiveSpec] = useState<string>("all");

  useEffect(() => {
    fetch("/api/doctors")
      .then((r) => r.ok ? r.json() : [])
      .then((data: Doctor[]) => {
        const seen = new Set<string>();
        const real = data
          .filter((d) =>
            d.is_available &&
            !!d.profile_photo_url &&
            d.full_name &&
            d.full_name.length > 5 &&
            !/^(test|yest|demo)\b/i.test(d.full_name)
          )
          .map((d) => ({ ...d, full_name: cleanName(d.full_name) }))
          .filter((d) => {
            const key = dedupKey(d.full_name);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
          });
        setDoctors(real);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const specialties = useMemo(() => {
    const all = new Set<string>();
    doctors.forEach((d) => {
      const spec = (d.specialties && d.specialties[0]) || d.specialty;
      if (spec) all.add(spec);
    });
    return ["all", ...Array.from(all)];
  }, [doctors]);

  const filtered = doctors.filter((d) => {
    const q = search.trim().toLowerCase();
    const matchesQ = !q || d.full_name.toLowerCase().includes(q) || (d.bio || "").toLowerCase().includes(q);
    const docSpec = (d.specialties && d.specialties[0]) || d.specialty;
    const matchesSpec = activeSpec === "all" || docSpec === activeSpec;
    return matchesQ && matchesSpec;
  });

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto overflow-x-hidden lm-doctors">
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        .lm-doctors {
          --cream: #FFFBF7;
          --cream-deep: #FFF3E8;
          --ivory: #FEFCF9;
          --terra: #D4725C;
          --teal: #35C8BB;
          --navy: #1A2540;
          --warm-gray: #6B6560;
          --warm-border: #EDE8E3;
          --warm-shadow: rgba(26, 37, 64, 0.06);
          font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
          background: var(--cream);
          color: var(--navy);
        }
        .lm-doctors .font-editorial { font-family: 'Fraunces', Georgia, serif; }
        .lm-doctors .doctor-card {
          transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.4s cubic-bezier(0.22, 1, 0.36, 1);
        }
        .lm-doctors .doctor-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 40px rgba(26, 37, 64, 0.08);
        }
      `}</style>

      {/* Sticky nav */}
      <nav className="sticky top-0 z-40 backdrop-blur-2xl border-b" style={{ background: 'rgba(255,251,247,0.9)', borderColor: 'var(--warm-border)' }}>
        <div className="max-w-6xl mx-auto px-6 sm:px-10 h-[72px] flex items-center justify-between">
          <Link href="/landing" className="flex items-center gap-3">
            <Image src="/logo-icon.png" alt="LongiMed" width={32} height={32} className="rounded-lg" />
            <span className="font-editorial text-[18px] font-semibold tracking-tight" style={{ color: 'var(--navy)' }}>
              LongiMed
            </span>
          </Link>
          <Link
            href="/landing"
            className="text-[13px] font-medium hover:opacity-70 transition-opacity inline-flex items-center gap-1.5"
            style={{ color: 'var(--warm-gray)' }}
          >
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            Back to home
          </Link>
        </div>
      </nav>

      {/* Header */}
      <section className="max-w-6xl mx-auto px-6 sm:px-10 pt-12 sm:pt-16 pb-8">
        <p className="text-[12px] font-semibold uppercase tracking-[0.2em] mb-4" style={{ color: 'var(--terra)' }}>
          Our doctors
        </p>
        <h1 className="font-editorial font-medium text-[40px] sm:text-[56px] leading-[1.05] tracking-[-0.02em] mb-5" style={{ color: 'var(--navy)' }}>
          Verified Ethiopian{" "}
          <span className="italic" style={{ color: 'var(--terra)' }}>physicians</span>
        </h1>
        <p className="text-[16px] leading-[1.65] max-w-xl" style={{ color: 'var(--warm-gray)' }}>
          Tap any card to start a consultation on Telegram. Or message us on WhatsApp / call to talk to the team first.
        </p>
      </section>

      {/* Filters */}
      <section className="max-w-6xl mx-auto px-6 sm:px-10 pb-8">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
          {/* Search */}
          <div className="relative flex-1">
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--warm-gray)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.2-5.2M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
            </svg>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name or specialty…"
              className="w-full pl-11 pr-4 py-3 rounded-full text-[14px] outline-none focus:ring-2 transition-shadow"
              style={{ background: 'var(--ivory)', border: '1px solid var(--warm-border)', color: 'var(--navy)' }}
            />
          </div>
          {/* Specialty pills */}
          <div className="flex gap-1.5 overflow-x-auto sm:flex-wrap pb-1 sm:pb-0 scrollbar-hide -mx-1 px-1">
            {specialties.map((s) => {
              const active = activeSpec === s;
              return (
                <button
                  key={s}
                  onClick={() => setActiveSpec(s)}
                  className={`px-3 py-1.5 rounded-full text-[12px] font-semibold whitespace-nowrap transition-colors ${active ? 'text-white' : ''}`}
                  style={{
                    background: active ? 'var(--navy)' : 'var(--ivory)',
                    border: `1px solid ${active ? 'var(--navy)' : 'var(--warm-border)'}`,
                    color: active ? '#fff' : 'var(--warm-gray)',
                  }}
                >
                  {s === "all" ? "All specialties" : (SPEC_LABELS[s] || s)}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Grid */}
      <section className="max-w-6xl mx-auto px-6 sm:px-10 pb-24">
        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="rounded-[20px] overflow-hidden animate-pulse" style={{ background: '#FFF', border: '1px solid var(--warm-border)' }}>
                <div className="w-full" style={{ aspectRatio: '4/5', background: 'var(--cream-deep)' }} />
                <div className="p-6 space-y-3">
                  <div className="h-5 rounded w-3/4" style={{ background: 'var(--cream-deep)' }} />
                  <div className="h-4 rounded w-1/2" style={{ background: 'var(--cream-deep)' }} />
                  <div className="h-3 rounded w-full" style={{ background: 'var(--cream-deep)' }} />
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <p className="font-editorial text-[20px] mb-2" style={{ color: 'var(--navy)' }}>No doctors match your search</p>
            <p className="text-[14px]" style={{ color: 'var(--warm-gray)' }}>Try a different specialty or clear the search field.</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {filtered.map((doc, i) => {
              const specLabel = SPEC_LABELS[(doc.specialties || [doc.specialty])[0]] || doc.specialty;
              return (
                <article
                  key={doc.id}
                  className="doctor-card rounded-[20px] overflow-hidden flex flex-col"
                  style={{
                    background: '#FFFFFF',
                    border: '1px solid var(--warm-border)',
                    boxShadow: '0 4px 20px var(--warm-shadow)',
                  }}
                >
                  {/* Portrait */}
                  <div className="relative w-full" style={{ aspectRatio: '4/5', background: i % 2 === 0 ? 'rgba(53,200,187,0.08)' : 'rgba(212,114,92,0.08)' }}>
                    {doc.profile_photo_url && (
                      <img src={doc.profile_photo_url} alt={doc.full_name} className="w-full h-full object-cover" />
                    )}
                    <div className="absolute inset-x-0 bottom-0 h-24" style={{ background: 'linear-gradient(to top, rgba(26,37,64,0.4), transparent)' }} />
                    {doc.is_available && (
                      <div className="absolute top-4 left-4 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold backdrop-blur" style={{ background: 'rgba(255,255,255,0.92)', color: '#059669' }}>
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                        Online
                      </div>
                    )}
                    {doc.rating_avg > 0 && (
                      <div className="absolute top-4 right-4 flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold backdrop-blur" style={{ background: 'rgba(255,255,255,0.92)', color: '#B8860B' }}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
                        {doc.rating_avg.toFixed(1)}
                      </div>
                    )}
                  </div>

                  {/* Body */}
                  <div className="p-6 sm:p-7 flex flex-col flex-1">
                    <h3 className="font-editorial font-medium text-[22px] mb-1 leading-[1.2]" style={{ color: 'var(--navy)' }}>
                      Dr. {doc.full_name}
                    </h3>
                    <p className="text-[13px] font-semibold mb-4" style={{ color: 'var(--teal)' }}>
                      {specLabel}
                    </p>
                    {doc.bio ? (
                      <p className="text-[14px] leading-[1.65] mb-5 flex-1" style={{ color: 'var(--warm-gray)' }}>
                        {doc.bio}
                      </p>
                    ) : (
                      <p className="text-[13px] italic mb-5 flex-1" style={{ color: 'var(--warm-gray)' }}>
                        Bio coming soon.
                      </p>
                    )}

                    {/* Languages */}
                    {doc.languages && doc.languages.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-5">
                        {doc.languages.map((lang) => (
                          <span
                            key={lang}
                            className="text-[11px] font-medium px-2.5 py-1 rounded-full"
                            style={{ background: 'var(--cream)', color: 'var(--warm-gray)' }}
                          >
                            {LANG_LABELS[lang] || lang}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Contact actions */}
                    <div className="flex items-center gap-2 mt-auto">
                      <a
                        href={`${BOT_LINK}?start=book_doctor_${doc.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-full text-[13px] font-semibold text-white active:scale-[0.97] transition-transform"
                        style={{ background: 'var(--navy)' }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.14.14 0 00-.07-.2c-.08-.06-.19-.04-.27-.02-.12.02-1.96 1.25-5.54 3.66-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.37-.49 1.02-.75 3.98-1.73 6.64-2.88 7.97-3.44 3.8-1.58 4.59-1.86 5.1-1.87.11 0 .37.03.54.17.14.12.18.28.2.45 0 .06.01.24 0 .37z"/></svg>
                        Book on Telegram
                      </a>
                      <a
                        href={`https://wa.me/${WA_DIGITS}?text=${encodeURIComponent(`Hi LongiMed — I'd like to book Dr. ${doc.full_name}.`)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`WhatsApp about Dr. ${doc.full_name}`}
                        className="w-10 h-10 rounded-full flex items-center justify-center text-white active:scale-95 transition-transform shrink-0"
                        style={{ background: '#25D366' }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 018.413 3.488 11.824 11.824 0 013.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 001.51 5.26l.601.957-1.022 3.733 3.84-1.007.56.36zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.149-.173.198-.297.297-.495.099-.198.05-.372-.025-.521-.074-.149-.669-1.612-.916-2.207-.241-.579-.486-.5-.669-.51l-.57-.01a1.094 1.094 0 00-.793.372c-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.876 1.213 3.074.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
                      </a>
                      <a
                        href={`tel:${CALL.replace(/\s/g, "")}`}
                        aria-label="Call LongiMed"
                        className="w-10 h-10 rounded-full flex items-center justify-center active:scale-95 transition-transform shrink-0"
                        style={{ background: 'var(--ivory)', border: '1px solid var(--warm-border)', color: 'var(--navy)' }}
                      >
                        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                      </a>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Floating WhatsApp */}
      <a
        href={`https://wa.me/${WA_DIGITS}?text=${encodeURIComponent("Hi LongiMed — I'd like to ask about a consultation.")}`}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Chat on WhatsApp"
        className="fixed bottom-5 right-5 sm:bottom-7 sm:right-7 z-[60] flex items-center justify-center w-14 h-14 sm:w-[60px] sm:h-[60px] rounded-full text-white"
        style={{ background: '#25D366', boxShadow: '0 8px 24px rgba(37, 211, 102, 0.35)' }}
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 018.413 3.488 11.824 11.824 0 013.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 001.51 5.26l.601.957-1.022 3.733 3.84-1.007.56.36zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.149-.173.198-.297.297-.495.099-.198.05-.372-.025-.521-.074-.149-.669-1.612-.916-2.207-.241-.579-.486-.5-.669-.51l-.57-.01a1.094 1.094 0 00-.793.372c-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.876 1.213 3.074.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
      </a>
    </div>
  );
}
