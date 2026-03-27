"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import { initTelegram } from "@/lib/telegram";
import { fetchQuestions } from "@/lib/api";
import type { Question } from "@/lib/api";
import { t, specLabel } from "@/lib/i18n";

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  general: { bg: "bg-brand-teal-light", text: "text-brand-teal-deep" },
  pediatrics: { bg: "bg-amber-50", text: "text-amber-700" },
  obgyn: { bg: "bg-pink-50", text: "text-pink-700" },
  dermatology: { bg: "bg-violet-50", text: "text-violet-700" },
  mental_health: { bg: "bg-indigo-50", text: "text-indigo-700" },
  cardiology: { bg: "bg-rose-50", text: "text-rose-700" },
  other: { bg: "bg-slate-50", text: "text-slate-600" },
};

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    ANSWERED: "bg-emerald-50 border-emerald-200 text-emerald-700",
    PENDING: "bg-amber-50 border-amber-200 text-amber-700",
    APPROVED: "bg-brand-blue-light border-blue-200 text-brand-blue",
    REJECTED: "bg-red-50 border-red-200 text-red-600",
  };
  const labels: Record<string, string> = { ANSWERED: t("qa_answered"), PENDING: t("qa_pending") };
  return (
    <span className={`inline-flex px-2 py-[2px] rounded-lg text-[10px] font-semibold border ${styles[status] || styles.PENDING}`}>
      {labels[status] || status.charAt(0) + status.slice(1).toLowerCase()}
    </span>
  );
}

export default function QAFeed() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initTelegram();
    fetchQuestions().then(setQuestions).catch(() => setQuestions([])).finally(() => setLoading(false));
  }, []);

  return (
    <div className="pt-5 pb-24">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight mb-1">{t("qa_title")}</h1>
        <p className="text-ink-secondary text-[14px]">{t("qa_subtitle")}</p>
      </motion.div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-4"><div className="space-y-2.5"><div className="h-4 skeleton w-1/4" /><div className="h-4 skeleton w-full" /><div className="h-3 skeleton w-3/5" /></div></div>
          ))}
        </div>
      ) : questions.length > 0 ? (
        <div className="space-y-3">
          {questions.map((q, i) => {
            const cat = CATEGORY_COLORS[q.category] || CATEGORY_COLORS.other;
            return (
              <motion.div key={q.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}>
                <Link href={`/qa/${q.id}`}>
                  <div className="card card-interactive p-4 group">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <span className={`inline-flex px-2 py-[2px] rounded-lg text-[11px] font-semibold ${cat.bg} ${cat.text}`}>{specLabel(q.category)}</span>
                      <StatusBadge status={q.status} />
                    </div>
                    <p className="text-ink-rich text-[14px] font-medium leading-snug line-clamp-2 mb-2 group-hover:text-brand-teal transition-colors">{q.text}</p>
                    {q.answer_text && (
                      <p className="text-ink-secondary text-[13px] leading-relaxed line-clamp-2 bg-surface-muted rounded-xl px-3 py-2">
                        <span className="text-brand-teal font-semibold">Dr: </span>{q.answer_text}
                      </p>
                    )}
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-[11px] text-ink-muted">{new Date(q.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</span>
                      {q.is_anonymous && <span className="text-[10px] text-ink-muted bg-surface-muted px-2 py-0.5 rounded-lg">{t("sessions_anonymous")}</span>}
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <EmptyState icon="💬" title={t("qa_no_questions")} subtitle={t("qa_no_questions_sub")} />
      )}

      {!loading && questions.length > 0 && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="text-center text-[11px] text-ink-muted mt-5">
          {t("qa_questions_count", { count: questions.length })}
        </motion.p>
      )}

      <Link href="/qa/ask">
        <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3, type: "spring", stiffness: 260, damping: 20 }}
          className="fixed bottom-6 right-6 z-30 w-14 h-14 rounded-2xl bg-brand-teal text-white shadow-glow flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" /></svg>
        </motion.div>
      </Link>
    </div>
  );
}
