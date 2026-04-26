"use client";

import { useState, useEffect, Suspense } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { initTelegram, getTelegramUser } from "@/lib/telegram";
import { fetchDoctors, bookSession } from "@/lib/api";
import type { Doctor } from "@/lib/api";
import { t, specLabel } from "@/lib/i18n";

const SPECIALTIES = [
  { value: "general", icon: "🩺" },
  { value: "family_medicine", icon: "👨‍👩‍👧‍👦" },
  { value: "internal_medicine", icon: "💊" },
  { value: "pediatrics", icon: "👶" },
  { value: "obgyn", icon: "🤰" },
  { value: "surgery", icon: "🔪" },
  { value: "orthopedics", icon: "🦴" },
  { value: "dermatology", icon: "🧴" },
  { value: "mental_health", icon: "🧠" },
  { value: "cardiology", icon: "❤️" },
  { value: "neurology", icon: "🧬" },
  { value: "ent", icon: "👂" },
  { value: "ophthalmology", icon: "👁️" },
  { value: "other", icon: "➕" },
];

export default function BookPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">{t("loading")}</div>}>
      <BookConsultation />
    </Suspense>
  );
}

function BookConsultation() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedDoctor = searchParams.get("doctor");

  const [step, setStep] = useState(1);
  const [pkg, setPkg] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loadingDoctors, setLoadingDoctors] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<number | null>(
    preselectedDoctor ? Number(preselectedDoctor) : null
  );
  const [issueDescription, setIssueDescription] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [isPaid, setIsPaid] = useState(false);

  useEffect(() => {
    initTelegram();
    if (preselectedDoctor) {
      fetchDoctors().then((docs) => {
        setDoctors(docs);
        const doc = docs.find((d) => d.id === Number(preselectedDoctor));
        if (doc) {
          setSpecialty(doc.specialty);
          setStep(4);
        }
      });
    }
  }, [preselectedDoctor]);

  useEffect(() => {
    if (specialty && step >= 3 && !preselectedDoctor) {
      setLoadingDoctors(true);
      fetchDoctors()
        .then((docs) => setDoctors(docs.filter((d) => (d.specialties || [d.specialty]).includes(specialty) && d.is_available)))
        .catch(() => setDoctors([]))
        .finally(() => setLoadingDoctors(false));
    }
  }, [specialty, step, preselectedDoctor]);

  const selectedDoctorObj = doctors.find((d) => d.id === selectedDoctor);

  const handleSubmit = async () => {
    const tgId = getTelegramUser()?.id;
    if (!tgId || !selectedDoctor) {
      alert(t("book_alert_tg"));
      return;
    }
    setSubmitting(true);
    try {
      await bookSession({
        telegram_id: tgId,
        package: pkg,
        specialty,
        doctor_id: selectedDoctor,
        issue_description: issueDescription.trim(),
        is_anonymous: isAnonymous,
      });
      setSuccess(true);
      setIsPaid(pkg === "SINGLE");
    } catch {
      alert(t("book_alert_fail"));
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
          className="flex flex-col items-center justify-center py-16 px-6 text-center"
        >
          <div className="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center text-3xl mb-4">
            {isPaid ? "🏦" : "⏳"}
          </div>
          <h3 className="font-display font-bold text-ink-rich text-lg mb-1.5">
            {isPaid ? t("book_success_payment_title") : t("book_success_session_title")}
          </h3>
          {isPaid ? (
            <div className="mb-6">
              <p className="text-ink-secondary text-[14px] max-w-[300px] leading-relaxed mb-4">
                {t("book_success_transfer", { amount: "500 ETB" })}
              </p>
              <div className="card p-4 text-left mb-3">
                <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-2">{t("book_success_bank_title")}</p>
                <div className="space-y-1.5">
                  <p className="text-[13px] text-ink-body"><span className="text-ink-muted">{t("book_success_bank")}</span> {t("book_success_bank_value")}</p>
                  <p className="text-[13px] text-ink-body"><span className="text-ink-muted">{t("book_success_account")}</span> {t("book_success_account_value")}</p>
                  <p className="text-[13px] text-ink-body"><span className="text-ink-muted">{t("book_success_name")}</span> {t("book_success_name_value")}</p>
                </div>
              </div>
              <p className="text-[12px] text-ink-muted leading-relaxed">
                {t("book_success_receipt")}
              </p>
            </div>
          ) : (
            <p className="text-ink-secondary text-[14px] max-w-[280px] leading-relaxed mb-6">
              {t("book_success_awaiting")}
            </p>
          )}
          <button
            onClick={() => router.push("/sessions")}
            className="bg-brand-teal text-white rounded-2xl px-6 py-3 font-display font-bold text-[14px] hover:bg-brand-teal-deep transition-colors"
          >
            {t("book_success_view")}
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="pt-5 pb-8">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Link href="/doctors" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          {t("back")}
        </Link>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight mb-1">
          {t("book_title")}
        </h1>
        <p className="text-ink-secondary text-[14px]">{t("book_subtitle")}</p>
      </motion.div>

      {/* Step 1: Package */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="mb-6"
      >
        <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
          Step 1 of 6 — {t("book_step_package")}
        </p>
        <div className="space-y-2">
          <button
            onClick={() => { setPkg("FREE_TRIAL"); if (step < 2) setStep(2); }}
            className={`card p-4 w-full text-left transition-all ${
              pkg === "FREE_TRIAL" ? "border-brand-teal bg-brand-teal-light shadow-glow-sm" : "hover:border-brand-teal/30"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-[15px] font-display font-bold ${pkg === "FREE_TRIAL" ? "text-brand-teal-deep" : "text-ink-rich"}`}>
                  {t("book_free_trial")}
                </p>
                <p className="text-[12px] text-ink-muted mt-0.5">{t("book_free_trial_desc")}</p>
              </div>
              <span className="text-[13px] font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-xl">{t("book_free_label")}</span>
            </div>
          </button>
          <button
            onClick={() => { setPkg("SINGLE"); if (step < 2) setStep(2); }}
            className={`card p-4 w-full text-left transition-all ${
              pkg === "SINGLE" ? "border-brand-teal bg-brand-teal-light shadow-glow-sm" : "hover:border-brand-teal/30"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-[15px] font-display font-bold ${pkg === "SINGLE" ? "text-brand-teal-deep" : "text-ink-rich"}`}>
                  {t("book_single")}
                </p>
                <p className="text-[12px] text-ink-muted mt-0.5">{t("book_single_desc")}</p>
              </div>
              <span className="text-[13px] font-bold text-brand-gold bg-brand-gold-light px-3 py-1 rounded-xl">{t("book_single_price")}</span>
            </div>
          </button>
        </div>
      </motion.div>

      {/* Step 2: Specialty */}
      {step >= 2 && !preselectedDoctor && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 2 of 6 — {t("book_step_specialty")}
          </p>
          <div className="grid grid-cols-2 gap-2">
            {SPECIALTIES.map((spec) => (
              <button
                key={spec.value}
                onClick={() => { setSpecialty(spec.value); setSelectedDoctor(null); if (step < 3) setStep(3); }}
                className={`card p-3 text-left transition-all ${
                  specialty === spec.value ? "border-brand-teal bg-brand-teal-light shadow-glow-sm" : "hover:border-brand-teal/30"
                }`}
              >
                <span className="text-lg">{spec.icon}</span>
                <p className={`text-[13px] font-semibold mt-1 ${specialty === spec.value ? "text-brand-teal-deep" : "text-ink-rich"}`}>
                  {specLabel(spec.value)}
                </p>
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Step 3: Select Doctor */}
      {step >= 3 && !preselectedDoctor && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 3 of 6 — {t("book_step_doctor")}
          </p>
          {loadingDoctors ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="card p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl skeleton" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 skeleton w-2/3" />
                      <div className="h-3 skeleton w-1/3" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : doctors.length > 0 ? (
            <div className="space-y-2">
              {doctors.map((doc) => {
                const initials = doc.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2);
                return (
                  <button
                    key={doc.id}
                    onClick={() => { setSelectedDoctor(doc.id); if (step < 4) setStep(4); }}
                    className={`card p-4 w-full text-left transition-all ${
                      selectedDoctor === doc.id ? "border-brand-teal bg-brand-teal-light shadow-glow-sm" : "hover:border-brand-teal/30"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-teal flex items-center justify-center text-white font-display font-bold text-sm shrink-0">
                        {initials}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-[14px] font-semibold truncate ${selectedDoctor === doc.id ? "text-brand-teal-deep" : "text-ink-rich"}`}>
                          Dr. {doc.full_name.replace(/^\s*(dr\.?\s+)+/i, "")}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[12px] text-ink-secondary">
                            {doc.rating_avg > 0 ? `★ ${doc.rating_avg}` : t("book_new")}
                          </span>
                          <span className="text-[11px] text-emerald-600 font-semibold">{t("book_available")}</span>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="card p-6 text-center">
              <p className="text-ink-muted text-[13px]">{t("book_no_doctors")}</p>
            </div>
          )}
        </motion.div>
      )}

      {/* Step 4: Issue Description */}
      {step >= 4 && selectedDoctor && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step {preselectedDoctor ? "2 of 4" : "4 of 6"} — {t("book_step_issue")}
          </p>
          <textarea
            value={issueDescription}
            onChange={(e) => setIssueDescription(e.target.value)}
            placeholder={t("book_issue_placeholder")}
            rows={4}
            className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all resize-none"
          />
          {issueDescription.trim().length >= 5 && step < 5 && (
            <button
              onClick={() => setStep(5)}
              className="mt-2 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              {t("continue")}
            </button>
          )}
        </motion.div>
      )}

      {/* Step 5: Anonymous */}
      {step >= 5 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step {preselectedDoctor ? "3 of 4" : "5 of 6"} — {t("book_step_privacy")}
          </p>
          <div className="card p-4">
            <button
              onClick={() => { setIsAnonymous(!isAnonymous); if (step < 6) setStep(6); }}
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
                <p className="text-[14px] font-semibold text-ink-rich">{t("book_anonymous")}</p>
                <p className="text-[12px] text-ink-muted">{t("book_anonymous_desc")}</p>
              </div>
            </button>
          </div>
          {step === 5 && (
            <button
              onClick={() => setStep(6)}
              className="mt-3 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              {t("book_continue_no_anon")}
            </button>
          )}
        </motion.div>
      )}

      {/* Step 6: Review */}
      {step >= 6 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step {preselectedDoctor ? "4 of 4" : "6 of 6"} — {t("book_step_review")}
          </p>
          <div className="card p-4 mb-4 border-l-4 border-l-brand-teal">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">{t("book_label_package")}</span>
                <span className="text-[13px] font-semibold text-ink-rich">
                  {pkg === "FREE_TRIAL" ? t("book_free_trial") : `${t("book_single")} (${t("book_single_price")})`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">{t("book_label_specialty")}</span>
                <span className="text-[13px] font-semibold text-ink-rich">{specLabel(specialty)}</span>
              </div>
              {selectedDoctorObj && (
                <div className="flex justify-between">
                  <span className="text-[12px] text-ink-muted">{t("book_label_doctor")}</span>
                  <span className="text-[13px] font-semibold text-ink-rich">Dr. {selectedDoctorObj.full_name.replace(/^\s*(dr\.?\s+)+/i, "")}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">{t("book_label_anonymous")}</span>
                <span className="text-[13px] font-semibold text-ink-rich">{isAnonymous ? t("yes") : t("no")}</span>
              </div>
              {issueDescription && (
                <div className="pt-2 border-t border-surface-border">
                  <span className="text-[12px] text-ink-muted">{t("book_label_issue")}</span>
                  <p className="text-[13px] text-ink-body mt-0.5 leading-relaxed">{issueDescription}</p>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full bg-brand-teal text-white rounded-2xl py-3.5 font-display font-bold text-[15px] hover:bg-brand-teal-deep transition-colors disabled:opacity-50 shadow-glow"
          >
            {submitting ? t("book_booking") : pkg === "SINGLE" ? t("book_confirm_paid") : t("book_confirm_free")}
          </button>
        </motion.div>
      )}
    </div>
  );
}
