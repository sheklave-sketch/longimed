"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import DoctorCard from "@/components/DoctorCard";
import EmptyState from "@/components/EmptyState";
import { initTelegram } from "@/lib/telegram";
import type { Doctor } from "@/lib/api";
import { t, specLabel } from "@/lib/i18n";

const FILTER_SPECS = [
  "all", "general", "family_medicine", "internal_medicine", "pediatrics",
  "obgyn", "surgery", "orthopedics", "dermatology", "mental_health",
  "cardiology", "neurology", "ent", "ophthalmology", "other",
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
    const matchSpec = filter === "all" || (d.specialties || [d.specialty]).includes(filter);
    const matchSearch = !search || d.full_name.toLowerCase().includes(search.toLowerCase()) || d.specialty.includes(search.toLowerCase());
    return matchSpec && matchSearch;
  });

  const availableCount = doctors.filter((d) => d.is_available).length;

  return (
    <div className="pt-5">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <div className="flex items-end justify-between mb-1">
          <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight">
            {t("doctors_title")}
          </h1>
          <div className="flex items-center gap-1.5 pb-1">
            <span className="status-online" />
            <span className="text-[12px] font-semibold text-emerald-600">{availableCount} {t("doc_online")}</span>
          </div>
        </div>
        <p className="text-ink-secondary text-[14px]">{t("doctors_subtitle")}</p>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="mb-4">
        <div className="relative">
          <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-faint" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            placeholder={t("doctors_search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface-white border border-surface-border rounded-2xl pl-10 pr-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 shadow-soft transition-all"
          />
        </div>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }} className="flex gap-2 overflow-x-auto pb-4 scrollbar-hide">
        {FILTER_SPECS.map((spec) => (
          <button
            key={spec}
            onClick={() => setFilter(spec)}
            className={`shrink-0 px-3.5 py-[7px] rounded-xl text-[12px] font-semibold transition-all duration-200 ${
              filter === spec
                ? "bg-brand-teal text-white shadow-glow-sm"
                : "bg-surface-white border border-surface-border text-ink-secondary hover:border-brand-teal/30 hover:text-ink-body"
            }`}
          >
            {spec === "all" ? t("doctors_all") : specLabel(spec)}
          </button>
        ))}
      </motion.div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-4">
              <div className="flex items-center gap-4">
                <div className="w-[52px] h-[52px] rounded-2xl skeleton" />
                <div className="flex-1 space-y-2.5">
                  <div className="h-4 skeleton w-3/5" />
                  <div className="h-3 skeleton w-2/5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map((doctor, i) => (
            <DoctorCard key={doctor.id} doctor={doctor} index={i} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon="🔍"
          title={t("doctors_no_results")}
          subtitle={search ? t("doctors_no_match", { query: search }) : t("doctors_no_specialty")}
        />
      )}

      {!loading && filtered.length > 0 && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="text-center text-[11px] text-ink-muted mt-5 pb-2">
          {filtered.length} / {doctors.length}
        </motion.p>
      )}
    </div>
  );
}
