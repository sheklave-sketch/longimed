"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { openBotLink, initTelegram } from "@/lib/telegram";
import type { Doctor } from "@/lib/api";

const SPECIALTY_ICONS: Record<string, string> = {
  general: "🩺", pediatrics: "👶", obgyn: "🤰",
  dermatology: "🧴", mental_health: "🧠", cardiology: "❤️", other: "🏥",
};

export default function DoctorProfile() {
  const params = useParams();
  const router = useRouter();
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initTelegram();
    fetch(`/api/doctors/${params.id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(setDoctor)
      .catch(() => setDoctor(null))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="pt-8 flex flex-col items-center">
        <div className="w-24 h-24 rounded-2xl bg-navy-100 animate-pulse mb-4" />
        <div className="h-6 bg-navy-100 rounded w-48 animate-pulse mb-2" />
        <div className="h-4 bg-navy-50 rounded w-32 animate-pulse" />
      </div>
    );
  }

  if (!doctor) {
    return (
      <div className="pt-16 text-center">
        <p className="text-5xl mb-4">😔</p>
        <h2 className="font-display font-bold text-navy-500 text-xl">Doctor not found</h2>
        <button
          onClick={() => router.push("/")}
          className="mt-4 px-6 py-2 bg-teal-400 text-white rounded-full text-sm font-medium"
        >
          ← Back to Directory
        </button>
      </div>
    );
  }

  const specIcon = SPECIALTY_ICONS[doctor.specialty] || "🏥";
  const initials = doctor.full_name
    .split(" ").map((n) => n[0]).join("").slice(0, 2);

  return (
    <div className="pt-4 pb-24">
      {/* Back */}
      <motion.button
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        onClick={() => router.push("/")}
        className="flex items-center gap-1 text-navy-300 text-sm mb-6 hover:text-teal-500 transition-colors"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Back to doctors
      </motion.button>

      {/* Profile header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-3xl p-6 shadow-glass-lg text-center mb-4"
      >
        <div className="relative inline-block mb-4">
          <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-teal-400 to-sky-400 flex items-center justify-center text-white font-display font-bold text-3xl shadow-glow mx-auto">
            {initials}
          </div>
          <div
            className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-3 border-white flex items-center justify-center ${
              doctor.is_available ? "bg-emerald-400" : "bg-red-400"
            }`}
          >
            <span className="text-white text-[8px]">
              {doctor.is_available ? "✓" : "—"}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-center gap-1.5 mb-1">
          <h1 className="font-display font-bold text-xl text-navy-600">
            Dr. {doctor.full_name}
          </h1>
          <span className="inline-flex w-5 h-5 rounded-full bg-teal-400 items-center justify-center badge-verified">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 6L5 8L9 3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
        </div>

        <p className="text-navy-300 text-sm">
          {specIcon} {doctor.specialty.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
        </p>

        {/* Rating */}
        <div className="flex items-center justify-center gap-4 mt-4 text-sm">
          <div className="text-center">
            <p className="font-display font-bold text-lg text-navy-600">
              {doctor.rating_avg > 0 ? `${doctor.rating_avg}` : "—"}
            </p>
            <p className="text-navy-200 text-xs">Rating</p>
          </div>
          <div className="w-px h-8 bg-navy-100" />
          <div className="text-center">
            <p className="font-display font-bold text-lg text-navy-600">
              {doctor.rating_count}
            </p>
            <p className="text-navy-200 text-xs">Reviews</p>
          </div>
          <div className="w-px h-8 bg-navy-100" />
          <div className="text-center">
            <p className="font-display font-bold text-lg text-navy-600">
              {doctor.languages.map((l) => l === "am" ? "🇪🇹" : "🇬🇧").join(" ")}
            </p>
            <p className="text-navy-200 text-xs">Languages</p>
          </div>
        </div>
      </motion.div>

      {/* Details */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass rounded-2xl p-5 shadow-glass space-y-4 mb-4"
      >
        {doctor.bio && (
          <div>
            <h3 className="font-display font-semibold text-navy-500 text-sm mb-1">About</h3>
            <p className="text-navy-400 text-sm leading-relaxed">{doctor.bio}</p>
          </div>
        )}

        <div className="flex items-center gap-2 text-sm">
          <span className="text-navy-200">📋</span>
          <span className="text-navy-400">License:</span>
          <span className="font-mono text-navy-500 text-xs bg-navy-50 px-2 py-0.5 rounded">
            {doctor.license_number}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <span className="text-navy-200">🟢</span>
          <span className="text-navy-400">Status:</span>
          <span className={`font-medium ${doctor.is_available ? "text-emerald-500" : "text-red-400"}`}>
            {doctor.is_available ? "Available for consultations" : "Currently unavailable"}
          </span>
        </div>
      </motion.div>

      {/* CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="fixed bottom-0 left-0 right-0 p-4 glass border-t border-white/30"
      >
        <div className="max-w-lg mx-auto">
          <button
            onClick={() => openBotLink(`book_doctor_${doctor.id}`)}
            disabled={!doctor.is_available}
            className={`
              w-full py-3.5 rounded-2xl font-display font-semibold text-sm transition-all duration-300
              ${doctor.is_available
                ? "bg-gradient-to-r from-teal-400 to-sky-400 text-white shadow-glow hover:shadow-glow/60 active:scale-[0.98]"
                : "bg-navy-100 text-navy-300 cursor-not-allowed"
              }
            `}
          >
            {doctor.is_available ? "Book Consultation →" : "Doctor Currently Unavailable"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
