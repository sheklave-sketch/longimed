"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import DoctorCard from "@/components/DoctorCard";
import EmptyState from "@/components/EmptyState";
import { initTelegram } from "@/lib/telegram";
import { searchQuestions, searchDoctors } from "@/lib/api";
import type { Question, Doctor } from "@/lib/api";

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  general: { bg: "bg-brand-teal-light", text: "text-brand-teal-deep" },
  pediatrics: { bg: "bg-amber-50", text: "text-amber-700" },
  obgyn: { bg: "bg-pink-50", text: "text-pink-700" },
  dermatology: { bg: "bg-violet-50", text: "text-violet-700" },
  mental_health: { bg: "bg-indigo-50", text: "text-indigo-700" },
  cardiology: { bg: "bg-rose-50", text: "text-rose-700" },
  other: { bg: "bg-slate-50", text: "text-slate-600" },
};

export default function SearchPage() {
  const [tab, setTab] = useState<"qa" | "doctors">("qa");
  const [query, setQuery] = useState("");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    initTelegram();
  }, []);

  const doSearch = useCallback(async (q: string, activeTab: "qa" | "doctors") => {
    if (q.trim().length < 2) {
      setQuestions([]);
      setDoctors([]);
      setSearched(false);
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      if (activeTab === "qa") {
        const results = await searchQuestions(q);
        setQuestions(results);
      } else {
        const results = await searchDoctors(q);
        setDoctors(results);
      }
    } catch {
      if (activeTab === "qa") setQuestions([]);
      else setDoctors([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      doSearch(query, tab);
    }, 400);
    return () => clearTimeout(timer);
  }, [query, tab, doSearch]);

  return (
    <div className="pt-5 pb-8">
      {/* Back */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Link href="/" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back
        </Link>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-5">
        <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight mb-1">
          Search
        </h1>
        <p className="text-ink-secondary text-[14px]">Find questions or doctors</p>
      </motion.div>

      {/* Tab switcher */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="mb-4">
        <div className="flex bg-surface-muted rounded-xl p-0.5 w-fit">
          {(["qa", "doctors"] as const).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setSearched(false); }}
              className={`px-4 py-2 rounded-lg text-[13px] font-semibold transition-all duration-200 ${
                tab === t
                  ? "bg-surface-white text-brand-teal shadow-soft"
                  : "text-ink-muted hover:text-ink-body"
              }`}
            >
              {t === "qa" ? "Q&A" : "Doctors"}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Search input */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mb-5">
        <div className="relative">
          <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-faint" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={tab === "qa" ? "Search questions..." : "Search doctors..."}
            className="w-full bg-surface-white border border-surface-border rounded-2xl pl-10 pr-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 shadow-soft transition-all"
          />
        </div>
      </motion.div>

      {/* Results */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-4">
              <div className="space-y-2.5">
                <div className="h-4 skeleton w-2/3" />
                <div className="h-3 skeleton w-full" />
              </div>
            </div>
          ))}
        </div>
      ) : tab === "qa" ? (
        searched && questions.length === 0 ? (
          <EmptyState
            icon="🔍"
            title="No questions found"
            subtitle={query ? `No matches for "${query}"` : "Type to search questions"}
          />
        ) : (
          <div className="space-y-3">
            {questions.map((q, i) => {
              const cat = CATEGORY_COLORS[q.category] || CATEGORY_COLORS.other;
              return (
                <motion.div
                  key={q.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.45, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                >
                  <Link href={`/qa/${q.id}`}>
                    <div className="card card-interactive p-4 group">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`inline-flex px-2 py-[2px] rounded-lg text-[11px] font-semibold ${cat.bg} ${cat.text}`}>
                          {q.category.replace("_", " ")}
                        </span>
                        <span className={`inline-flex px-2 py-[2px] rounded-lg text-[10px] font-semibold border ${
                          q.status === "ANSWERED"
                            ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                            : "bg-amber-50 border-amber-200 text-amber-700"
                        }`}>
                          {q.status.charAt(0) + q.status.slice(1).toLowerCase()}
                        </span>
                      </div>
                      <p className="text-ink-rich text-[14px] font-medium leading-snug line-clamp-2 group-hover:text-brand-teal transition-colors">
                        {q.text}
                      </p>
                      {q.answer_text && (
                        <p className="text-ink-secondary text-[12px] leading-relaxed line-clamp-1 mt-1.5">
                          <span className="text-brand-teal font-semibold">A: </span>{q.answer_text}
                        </p>
                      )}
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )
      ) : (
        searched && doctors.length === 0 ? (
          <EmptyState
            icon="🔍"
            title="No doctors found"
            subtitle={query ? `No matches for "${query}"` : "Type to search doctors"}
          />
        ) : (
          <div className="space-y-3">
            {doctors.map((doctor, i) => (
              <DoctorCard key={doctor.id} doctor={doctor} index={i} />
            ))}
          </div>
        )
      )}

      {!loading && !searched && (
        <div className="flex flex-col items-center py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-surface-muted flex items-center justify-center text-2xl mb-3">
            🔍
          </div>
          <p className="text-ink-muted text-[14px]">Start typing to search</p>
        </div>
      )}
    </div>
  );
}
