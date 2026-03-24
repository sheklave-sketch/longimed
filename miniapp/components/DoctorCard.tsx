"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { Doctor } from "@/lib/api";

const SPECIALTY_COLORS: Record<string, string> = {
  general: "bg-teal-50 text-teal-700",
  pediatrics: "bg-amber-50 text-amber-700",
  obgyn: "bg-pink-50 text-pink-700",
  dermatology: "bg-violet-50 text-violet-700",
  mental_health: "bg-indigo-50 text-indigo-700",
  cardiology: "bg-red-50 text-red-700",
  other: "bg-slate-50 text-slate-600",
};

const SPECIALTY_ICONS: Record<string, string> = {
  general: "🩺",
  pediatrics: "👶",
  obgyn: "🤰",
  dermatology: "🧴",
  mental_health: "🧠",
  cardiology: "❤️",
  other: "🏥",
};

export default function DoctorCard({
  doctor,
  index = 0,
}: {
  doctor: Doctor;
  index?: number;
}) {
  const specColor = SPECIALTY_COLORS[doctor.specialty] || SPECIALTY_COLORS.other;
  const specIcon = SPECIALTY_ICONS[doctor.specialty] || "🏥";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
    >
      <Link href={`/doctor/${doctor.id}`}>
        <div className="glass rounded-2xl p-4 shadow-glass hover:shadow-glass-lg transition-all duration-300 hover:-translate-y-0.5 group">
          <div className="flex items-start gap-3.5">
            {/* Avatar */}
            <div className="relative shrink-0">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-400 to-sky-400 flex items-center justify-center text-white font-display font-bold text-lg shadow-glow/40">
                {doctor.full_name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .slice(0, 2)}
              </div>
              <div
                className={`absolute -bottom-0.5 -right-0.5 ${
                  doctor.is_available ? "dot-available" : "dot-unavailable"
                } border-2 border-white`}
              />
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <h3 className="font-display font-semibold text-navy-600 truncate group-hover:text-teal-600 transition-colors">
                  Dr. {doctor.full_name}
                </h3>
                <span className="inline-flex w-4 h-4 rounded-full bg-teal-400 items-center justify-center badge-verified shrink-0">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                    <path d="M2.5 5L4.5 7L7.5 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
              </div>

              <div className="flex items-center gap-2 mt-1">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${specColor}`}>
                  {specIcon} {doctor.specialty.replace("_", " ")}
                </span>
                {doctor.languages.length > 0 && (
                  <span className="text-[11px] text-navy-300">
                    {doctor.languages.includes("am") && "🇪🇹"}
                    {doctor.languages.includes("en") && "🇬🇧"}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 mt-2 text-xs text-navy-400">
                <span className="flex items-center gap-0.5">
                  <span className="text-amber-400">★</span>
                  {doctor.rating_avg > 0
                    ? `${doctor.rating_avg}/5 (${doctor.rating_count})`
                    : "New"}
                </span>
                <span className={doctor.is_available ? "text-emerald-500 font-medium" : "text-navy-300"}>
                  {doctor.is_available ? "Available" : "Busy"}
                </span>
              </div>
            </div>

            {/* Arrow */}
            <div className="text-navy-200 group-hover:text-teal-400 transition-colors self-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7.5 5L12.5 10L7.5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
