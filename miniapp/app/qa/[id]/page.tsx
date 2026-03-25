"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useParams } from "next/navigation";
import { initTelegram, getTelegramUser } from "@/lib/telegram";
import { fetchQuestionDetail, submitFollowUp } from "@/lib/api";
import type { QuestionDetail } from "@/lib/api";

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  general: { bg: "bg-brand-teal-light", text: "text-brand-teal-deep" },
  pediatrics: { bg: "bg-amber-50", text: "text-amber-700" },
  obgyn: { bg: "bg-pink-50", text: "text-pink-700" },
  dermatology: { bg: "bg-violet-50", text: "text-violet-700" },
  mental_health: { bg: "bg-indigo-50", text: "text-indigo-700" },
  cardiology: { bg: "bg-rose-50", text: "text-rose-700" },
  other: { bg: "bg-slate-50", text: "text-slate-600" },
};

export default function QuestionDetailPage() {
  const params = useParams();
  const questionId = Number(params.id);
  const [question, setQuestion] = useState<QuestionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [followUpText, setFollowUpText] = useState("");
  const [followUpAnon, setFollowUpAnon] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    initTelegram();
    fetchQuestionDetail(questionId)
      .then(setQuestion)
      .catch(() => setQuestion(null))
      .finally(() => setLoading(false));
  }, [questionId]);

  const handleSubmitFollowUp = async () => {
    const tgId = getTelegramUser()?.id;
    if (!tgId || !followUpText.trim()) return;
    setSubmitting(true);
    try {
      await submitFollowUp(questionId, {
        telegram_id: tgId,
        text: followUpText.trim(),
        is_anonymous: followUpAnon,
      });
      setSubmitSuccess(true);
      setFollowUpText("");
      setShowFollowUp(false);
      // Refetch to show new follow-up
      const updated = await fetchQuestionDetail(questionId);
      setQuestion(updated);
    } catch {
      alert("Failed to submit follow-up. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="pt-5 space-y-4">
        <div className="h-4 skeleton w-20" />
        <div className="card p-5 space-y-3">
          <div className="h-5 skeleton w-1/3" />
          <div className="h-4 skeleton w-full" />
          <div className="h-4 skeleton w-4/5" />
        </div>
        <div className="card p-5 space-y-3">
          <div className="h-4 skeleton w-1/4" />
          <div className="h-4 skeleton w-full" />
        </div>
      </div>
    );
  }

  if (!question) {
    return (
      <div className="pt-5">
        <Link href="/qa" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-6">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back to Q&A
        </Link>
        <div className="flex flex-col items-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface-muted flex items-center justify-center text-3xl mb-4">
            🔍
          </div>
          <h3 className="font-display font-semibold text-ink-rich text-base">Question not found</h3>
          <p className="text-ink-secondary text-sm mt-1.5">This question may have been removed.</p>
        </div>
      </div>
    );
  }

  const cat = CATEGORY_COLORS[question.category] || CATEGORY_COLORS.other;
  const approvedFollowUps = question.follow_ups.filter((f) => f.status === "APPROVED");

  return (
    <div className="pt-5 pb-8">
      {/* Back */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Link href="/qa" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back to Q&A
        </Link>
      </motion.div>

      {/* Question card */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="card p-5 mb-4"
      >
        <div className="flex items-center gap-2 mb-3">
          <span className={`inline-flex px-2 py-[2px] rounded-lg text-[11px] font-semibold ${cat.bg} ${cat.text}`}>
            {question.category.replace("_", " ")}
          </span>
          {question.is_anonymous && (
            <span className="text-[10px] text-ink-muted bg-surface-muted px-2 py-0.5 rounded-lg">Anonymous</span>
          )}
          <span className={`ml-auto inline-flex px-2 py-[2px] rounded-lg text-[10px] font-semibold border ${
            question.status === "ANSWERED"
              ? "bg-emerald-50 border-emerald-200 text-emerald-700"
              : "bg-amber-50 border-amber-200 text-amber-700"
          }`}>
            {question.status.charAt(0) + question.status.slice(1).toLowerCase()}
          </span>
        </div>

        <p className="text-ink-rich text-[15px] font-medium leading-relaxed">
          {question.text}
        </p>

        <p className="text-[11px] text-ink-muted mt-3">
          {new Date(question.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
        </p>
      </motion.div>

      {/* Answer */}
      {question.answer_text && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="card p-5 mb-4 border-l-4 border-l-brand-teal"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-teal flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3.5 7L6 9.5L10.5 4.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
            <span className="font-display font-semibold text-[13px] text-ink-rich">
              {question.answered_by_name ? `Dr. ${question.answered_by_name}` : "Doctor"}
            </span>
          </div>
          <p className="text-ink-body text-[14px] leading-relaxed">
            {question.answer_text}
          </p>
          {question.answered_at && (
            <p className="text-[11px] text-ink-muted mt-2">
              {new Date(question.answered_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
            </p>
          )}
        </motion.div>
      )}

      {/* Follow-ups */}
      {approvedFollowUps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mb-4"
        >
          <h3 className="font-display font-semibold text-[14px] text-ink-rich mb-3">
            Follow-ups ({approvedFollowUps.length})
          </h3>
          <div className="space-y-2">
            {approvedFollowUps.map((fu) => (
              <div key={fu.id} className="card p-4">
                <p className="text-ink-body text-[13px] leading-relaxed">{fu.text}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[10px] text-ink-muted">
                    {new Date(fu.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                  </span>
                  {fu.is_anonymous && (
                    <span className="text-[10px] text-ink-muted bg-surface-muted px-1.5 py-0.5 rounded">Anonymous</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Success message */}
      {submitSuccess && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-4 mb-4 bg-emerald-50 border-emerald-200"
        >
          <p className="text-emerald-700 text-[13px] font-semibold">Follow-up submitted for review!</p>
        </motion.div>
      )}

      {/* Add follow-up */}
      {!showFollowUp ? (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          onClick={() => setShowFollowUp(true)}
          className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-secondary hover:border-brand-teal/30 hover:text-brand-teal transition-all text-center font-display font-semibold"
        >
          + Add Follow-Up
        </motion.button>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-4"
        >
          <h4 className="font-display font-semibold text-[13px] text-ink-rich mb-3">Add Follow-Up</h4>
          <textarea
            value={followUpText}
            onChange={(e) => setFollowUpText(e.target.value)}
            placeholder="Type your follow-up question..."
            rows={3}
            className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all resize-none"
          />

          <div className="flex items-center justify-between mt-3">
            <button
              onClick={() => setFollowUpAnon(!followUpAnon)}
              className="flex items-center gap-2 text-[13px] text-ink-secondary"
            >
              <div className={`w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all ${
                followUpAnon ? "bg-brand-teal border-brand-teal" : "border-surface-border-strong"
              }`}>
                {followUpAnon && (
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 5L4 7L8 3" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
                )}
              </div>
              Anonymous
            </button>

            <div className="flex gap-2">
              <button
                onClick={() => { setShowFollowUp(false); setFollowUpText(""); }}
                className="px-4 py-2 rounded-xl text-[13px] font-semibold text-ink-secondary bg-surface-muted hover:bg-surface-border transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitFollowUp}
                disabled={submitting || followUpText.trim().length < 5}
                className="px-4 py-2 rounded-xl text-[13px] font-display font-bold text-white bg-brand-teal hover:bg-brand-teal-deep transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {submitting ? "Sending..." : "Submit"}
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
