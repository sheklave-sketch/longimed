"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { Doctor } from "@/lib/api";

const SPEC_CONFIG: Record<string, { bg: string; text: string; icon: string }> = {
  general: { bg: "bg-brand-teal-light", text: "text-brand-teal-deep", icon: "🩺" },
  pediatrics: { bg: "bg-amber-50", text: "text-amber-700", icon: "👶" },
  obgyn: { bg: "bg-pink-50", text: "text-pink-700", icon: "🤰" },
  dermatology: { bg: "bg-violet-50", text: "text-violet-700", icon: "🧴" },
  mental_health: { bg: "bg-indigo-50", text: "text-indigo-700", icon: "🧠" },
  cardiology: { bg: "bg-rose-50", text: "text-rose-700", icon: "❤️" },
  other: { bg: "bg-slate-50", text: "text-slate-600", icon: "🏥" },
};

export default function DoctorCard({ doctor, index = 0 }: { doctor: Doctor; index?: number }) {
  const spec = SPEC_CONFIG[doctor.specialty] || SPEC_CONFIG.other;
  const initials = doctor.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.07, ease: [0.16, 1, 0.3, 1] }}
    >
      <Link href={`/doctor/${doctor.id}`}>
        <div className="card card-interactive p-4 group">
          <div className="flex items-center gap-4">
            {/* Avatar */}
            <div className="relative shrink-0">
              {doctor.profile_photo_url ? (
                <img src={doctor.profile_photo_url} alt={doctor.full_name} className="w-[52px] h-[52px] rounded-2xl object-cover shadow-glow-sm" />
              ) : (
                <div className="w-[52px] h-[52px] rounded-2xl bg-gradient-teal flex items-center justify-center text-white font-display font-bold text-lg shadow-glow-sm">
                  {initials}
                </div>
              )}
              <div className={`absolute -bottom-0.5 -right-0.5 ${doctor.is_available ? "status-online" : "status-offline"} ring-2 ring-white`} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-0.5">
                <h3 className="font-display font-semibold text-ink-rich text-[15px] truncate group-hover:text-brand-teal transition-colors">
                  Dr. {doctor.full_name}
                </h3>
                <span className="shrink-0 w-[18px] h-[18px] rounded-full bg-brand-teal flex items-center justify-center badge-verified">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2.5 5L4.5 7L7.5 3" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className={`inline-flex items-center gap-1 px-2 py-[2px] rounded-lg text-[11px] font-semibold ${spec.bg} ${spec.text}`}>
                  {spec.icon} {doctor.specialty.replace("_", " ")}
                </span>
                <span className="text-[11px] text-ink-muted">
                  {doctor.languages.includes("am") && "🇪🇹"}{doctor.languages.includes("en") && " 🇬🇧"}
                </span>
              </div>

              <div className="flex items-center gap-3 mt-1.5">
                <span className="flex items-center gap-1 text-[12px] text-ink-secondary">
                  <span className="text-brand-gold">★</span>
                  {doctor.rating_avg > 0 ? <><span className="font-semibold text-ink-body">{doctor.rating_avg}</span><span className="text-ink-muted">/5 · {doctor.rating_count}</span></> : <span className="text-ink-muted">New</span>}
                </span>
                <span className={`text-[11px] font-semibold ${doctor.is_available ? "text-emerald-600" : "text-ink-muted"}`}>
                  {doctor.is_available ? "Available" : "Busy"}
                </span>
              </div>
            </div>

            {/* Chevron */}
            <svg className="shrink-0 text-ink-faint group-hover:text-brand-teal transition-colors" width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M7.5 5L12.5 10L7.5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
