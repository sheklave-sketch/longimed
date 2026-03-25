"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getTelegramUser, initTelegram } from "@/lib/telegram";
import { submitQuestion } from "@/lib/api";
import { useEffect } from "react";

const CATEGORIES = [
  { value: "general", label: "General", icon: "🩺" },
  { value: "pediatrics", label: "Pediatrics", icon: "👶" },
  { value: "obgyn", label: "OB/GYN", icon: "🤰" },
  { value: "dermatology", label: "Dermatology", icon: "🧴" },
  { value: "mental_health", label: "Mental Health", icon: "🧠" },
  { value: "cardiology", label: "Cardiology", icon: "❤️" },
];

export default function AskQuestion() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    initTelegram();
  }, []);

  const handleSubmit = async () => {
    const tgId = getTelegramUser()?.id;
    if (!tgId) {
      alert("Please open this app from Telegram.");
      return;
    }
    setSubmitting(true);
    try {
      await submitQuestion({
        telegram_id: tgId,
        category,
        text: text.trim(),
        is_anonymous: isAnonymous,
      });
      setSuccess(true);
    } catch {
      alert("Failed to submit question. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="pt-5">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center justify-center py-20 px-6 text-center"
        >
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center text-3xl mb-4">
            ✅
          </div>
          <h3 className="font-display font-bold text-ink-rich text-lg mb-1.5">Question Submitted!</h3>
          <p className="text-ink-secondary text-[14px] max-w-[280px] leading-relaxed mb-6">
            Your question is pending review. A doctor will answer it soon.
          </p>
          <button
            onClick={() => router.push("/qa")}
            className="bg-brand-teal text-white rounded-2xl px-6 py-3 font-display font-bold text-[14px] hover:bg-brand-teal-deep transition-colors"
          >
            Back to Q&A
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="pt-5 pb-8">
      {/* Back */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Link href="/qa" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back to Q&A
        </Link>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight mb-1">
          Ask a Question
        </h1>
        <p className="text-ink-secondary text-[14px]">Get a free answer from a verified doctor</p>
      </motion.div>

      {/* Step 1: Category */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="mb-6"
      >
        <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
          Step 1 of 4 — Category
        </p>
        <div className="grid grid-cols-2 gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.value}
              onClick={() => { setCategory(cat.value); if (step < 2) setStep(2); }}
              className={`card p-3 text-left transition-all ${
                category === cat.value
                  ? "border-brand-teal bg-brand-teal-light shadow-glow-sm"
                  : "hover:border-brand-teal/30"
              }`}
            >
              <span className="text-lg">{cat.icon}</span>
              <p className={`text-[13px] font-semibold mt-1 ${category === cat.value ? "text-brand-teal-deep" : "text-ink-rich"}`}>
                {cat.label}
              </p>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Step 2: Anonymous toggle */}
      {step >= 2 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 2 of 4 — Privacy
          </p>
          <div className="card p-4">
            <button
              onClick={() => { setIsAnonymous(!isAnonymous); if (step < 3) setStep(3); }}
              className="flex items-center gap-3 w-full"
            >
              <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all shrink-0 ${
                isAnonymous ? "bg-brand-teal border-brand-teal" : "border-surface-border-strong"
              }`}>
                {isAnonymous && (
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2.5 6L5 8.5L9.5 3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                )}
              </div>
              <div className="text-left">
                <p className="text-[14px] font-semibold text-ink-rich">Ask anonymously</p>
                <p className="text-[12px] text-ink-muted">Your name won&apos;t be shown publicly</p>
              </div>
            </button>
          </div>
          {step === 2 && (
            <button
              onClick={() => setStep(3)}
              className="mt-3 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              Continue without anonymous →
            </button>
          )}
        </motion.div>
      )}

      {/* Step 3: Question text */}
      {step >= 3 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 3 of 4 — Your Question
          </p>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Describe your question in detail (minimum 10 characters)..."
            rows={5}
            className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all resize-none"
          />
          <div className="flex items-center justify-between mt-2">
            <span className={`text-[11px] ${text.length >= 10 ? "text-emerald-600" : "text-ink-muted"}`}>
              {text.length} / 10 min
            </span>
            {text.trim().length >= 10 && step < 4 && (
              <button
                onClick={() => setStep(4)}
                className="text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
              >
                Preview →
              </button>
            )}
          </div>
        </motion.div>
      )}

      {/* Step 4: Preview + Confirm */}
      {step >= 4 && text.trim().length >= 10 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 4 of 4 — Review
          </p>
          <div className="card p-4 mb-4 border-l-4 border-l-brand-teal">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex px-2 py-[2px] rounded-lg text-[11px] font-semibold bg-brand-teal-light text-brand-teal-deep">
                {category.replace("_", " ")}
              </span>
              {isAnonymous && (
                <span className="text-[10px] text-ink-muted bg-surface-muted px-2 py-0.5 rounded-lg">Anonymous</span>
              )}
            </div>
            <p className="text-ink-rich text-[14px] leading-relaxed">{text}</p>
          </div>

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full bg-brand-teal text-white rounded-2xl py-3.5 font-display font-bold text-[15px] hover:bg-brand-teal-deep transition-colors disabled:opacity-50 shadow-glow"
          >
            {submitting ? "Submitting..." : "Submit Question"}
          </button>
        </motion.div>
      )}
    </div>
  );
}
