"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { openBotLink, initTelegram } from "@/lib/telegram";
import type { Doctor } from "@/lib/api";

const SPEC_ICONS: Record<string, string> = {
  general: "🩺", family_medicine: "👨‍👩‍👧‍👦", internal_medicine: "💊",
  pediatrics: "👶", obgyn: "🤰", surgery: "🔪", orthopedics: "🦴",
  dermatology: "🧴", mental_health: "🧠", cardiology: "❤️",
  neurology: "🧬", ent: "👂", ophthalmology: "👁️", other: "🏥",
};

export default function DoctorProfile() {
  const params = useParams();
  const router = useRouter();
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initTelegram();
    fetch(`/api/doctors/${params.id}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setDoctor)
      .catch(() => setDoctor(null))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return (
    <div className="pt-10 flex flex-col items-center gap-3">
      <div className="w-20 h-20 rounded-3xl skeleton" />
      <div className="h-5 skeleton w-40" />
      <div className="h-4 skeleton w-28" />
    </div>
  );

  if (!doctor) return (
    <div className="pt-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-surface-muted flex items-center justify-center text-3xl mx-auto mb-4">😔</div>
      <h2 className="font-display font-bold text-ink-rich text-lg">Doctor not found</h2>
      <button onClick={() => router.push("/doctors")} className="mt-5 px-6 py-2.5 bg-brand-teal text-white rounded-2xl text-sm font-semibold shadow-glow-sm">
        ← Back to Directory
      </button>
    </div>
  );

  const allSpecs = doctor.specialties || [doctor.specialty];
  const specIcon = SPEC_ICONS[allSpecs[0]] || "🏥";
  const initials = doctor.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2);
  const specLabel = allSpecs.map((s) => s.replace("_", " ").replace(/\b\w/g, (c: string) => c.toUpperCase())).join(", ");

  return (
    <div className="pt-3 pb-28">
      {/* Back */}
      <motion.button initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
        onClick={() => router.push("/doctors")}
        className="flex items-center gap-1.5 text-ink-secondary text-[13px] font-medium mb-5 hover:text-brand-teal transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 3L5 7L9 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
        Back
      </motion.button>

      {/* Profile card */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="card p-6 text-center mb-4">
        {/* Avatar */}
        <div className="relative inline-block mb-4">
          {doctor.profile_photo_url ? (
            <img src={doctor.profile_photo_url} alt={doctor.full_name} className="w-20 h-20 rounded-3xl object-cover shadow-glow mx-auto" />
          ) : (
            <div className="w-20 h-20 rounded-3xl bg-gradient-teal flex items-center justify-center text-white font-display font-bold text-2xl shadow-glow mx-auto">
              {initials}
            </div>
          )}
          <div className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full ring-[3px] ring-white flex items-center justify-center ${doctor.is_available ? "bg-emerald-400" : "bg-gray-300"}`}>
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2.5 5L4.5 7L7.5 3" stroke="white" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </div>
        </div>

        {/* Name + badge */}
        <div className="flex items-center justify-center gap-2 mb-1">
          <h1 className="font-display font-bold text-[20px] text-ink-rich">Dr. {doctor.full_name}</h1>
          <span className="w-5 h-5 rounded-full bg-brand-teal flex items-center justify-center badge-verified">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M3 5.5L4.8 7.5L8 3.5" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </span>
        </div>
        <p className="text-ink-secondary text-[13px] font-medium">{specIcon} {specLabel}</p>

        {/* Stats row */}
        <div className="flex items-center justify-center mt-5 bg-surface-muted rounded-2xl p-3 divide-x divide-surface-border">
          <div className="flex-1 text-center">
            <p className="font-display font-bold text-[18px] text-ink-rich">{doctor.rating_avg > 0 ? doctor.rating_avg : "—"}</p>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">Rating</p>
          </div>
          <div className="flex-1 text-center">
            <p className="font-display font-bold text-[18px] text-ink-rich">{doctor.rating_count}</p>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">Reviews</p>
          </div>
          <div className="flex-1 text-center">
            <p className="text-[18px]">{doctor.languages.map((l) => l === "am" ? "🇪🇹" : "🇬🇧").join(" ")}</p>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">Languages</p>
          </div>
        </div>
      </motion.div>

      {/* Details card */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card p-5 space-y-4 mb-4">
        {doctor.bio && (
          <div>
            <h3 className="font-display font-semibold text-ink-rich text-[13px] mb-1.5">About</h3>
            <p className="text-ink-body text-[13px] leading-[1.7]">{doctor.bio}</p>
          </div>
        )}

        <div className="h-px bg-surface-border" />

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-teal-light flex items-center justify-center text-[14px]">📋</div>
          <div>
            <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">License</p>
            <p className="font-mono text-ink-body text-[13px] tracking-wide">{doctor.license_number}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[14px] ${doctor.is_available ? "bg-emerald-50" : "bg-surface-muted"}`}>
            {doctor.is_available ? "🟢" : "🔴"}
          </div>
          <div>
            <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">Status</p>
            <p className={`text-[13px] font-semibold ${doctor.is_available ? "text-emerald-600" : "text-ink-muted"}`}>
              {doctor.is_available ? "Available for consultations" : "Currently unavailable"}
            </p>
          </div>
        </div>
      </motion.div>

      {/* CTA */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
        className="fixed bottom-0 left-0 right-0 bottom-bar px-5 pt-6 pb-5"
      >
        <div className="max-w-lg mx-auto">
          <button
            onClick={() => router.push(`/book?doctor=${doctor.id}`)}
            disabled={!doctor.is_available}
            className={`w-full py-3.5 rounded-2xl font-display font-bold text-[15px] tracking-[-0.01em] transition-all duration-300 ${
              doctor.is_available
                ? "bg-gradient-teal text-white shadow-glow active:scale-[0.98]"
                : "bg-surface-muted text-ink-muted cursor-not-allowed"
            }`}
          >
            {doctor.is_available ? "Book Consultation →" : "Currently Unavailable"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
