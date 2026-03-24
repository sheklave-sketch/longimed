"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import DoctorCard from "@/components/DoctorCard";
import EmptyState from "@/components/EmptyState";
import { initTelegram } from "@/lib/telegram";
import type { Doctor } from "@/lib/api";

const SPECIALTIES = [
  { value: "all", label: "All", icon: "🏥" },
  { value: "general", label: "General", icon: "🩺" },
  { value: "pediatrics", label: "Pediatrics", icon: "👶" },
  { value: "obgyn", label: "OB/GYN", icon: "🤰" },
  { value: "dermatology", label: "Dermatology", icon: "🧴" },
  { value: "mental_health", label: "Mental Health", icon: "🧠" },
  { value: "cardiology", label: "Cardiology", icon: "❤️" },
];

export default function DoctorDirectory() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initTelegram();
    fetch("/api/doctors")
      .then((r) => r.json())
      .then(setDoctors)
      .catch(() => setDoctors([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = doctors.filter((d) => {
    const matchSpec = filter === "all" || d.specialty === filter;
    const matchSearch =
      !search ||
      d.full_name.toLowerCase().includes(search.toLowerCase()) ||
      d.specialty.includes(search.toLowerCase());
    return matchSpec && matchSearch;
  });

  return (
    <div className="pt-4">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-5"
      >
        <h1 className="font-display font-bold text-2xl text-navy-600">
          Our Doctors
        </h1>
        <p className="text-navy-300 text-sm mt-1">
          Verified Ethiopian medical professionals
        </p>
      </motion.div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-4"
      >
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 text-navy-200"
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
          >
            <circle cx="7.5" cy="7.5" r="5.5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M11.5 11.5L16 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            placeholder="Search by name or specialty..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full glass rounded-xl pl-10 pr-4 py-3 text-sm text-navy-600 placeholder:text-navy-200 focus:outline-none focus:ring-2 focus:ring-teal-400/30 shadow-glass"
          />
        </div>
      </motion.div>

      {/* Specialty filter pills */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15 }}
        className="flex gap-1.5 overflow-x-auto pb-3 mb-4 scrollbar-hide"
      >
        {SPECIALTIES.map((spec) => (
          <button
            key={spec.value}
            onClick={() => setFilter(spec.value)}
            className={`
              shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
              ${filter === spec.value
                ? "bg-teal-400 text-white shadow-glow"
                : "glass text-navy-400 hover:text-navy-600"
              }
            `}
          >
            {spec.icon} {spec.label}
          </button>
        ))}
      </motion.div>

      {/* Doctor list */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="glass rounded-2xl p-4 shadow-glass animate-pulse"
            >
              <div className="flex items-center gap-3.5">
                <div className="w-14 h-14 rounded-xl bg-navy-100" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-navy-100 rounded w-2/3" />
                  <div className="h-3 bg-navy-50 rounded w-1/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="flex flex-col gap-3">
          {filtered.map((doctor, i) => (
            <DoctorCard key={doctor.id} doctor={doctor} index={i} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon="🔍"
          title="No doctors found"
          subtitle={search ? `No results for "${search}"` : "No doctors in this specialty yet"}
        />
      )}

      {/* Count */}
      {!loading && filtered.length > 0 && (
        <p className="text-center text-xs text-navy-200 mt-4">
          Showing {filtered.length} of {doctors.length} doctors
        </p>
      )}
    </div>
  );
}
