"use client";

import { useState, useEffect, Suspense } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { initTelegram, getTelegramUser } from "@/lib/telegram";
import { fetchDoctors, bookSession } from "@/lib/api";
import type { Doctor } from "@/lib/api";

const SPECIALTIES = [
  { value: "general", label: "General / GP", icon: "🩺" },
  { value: "family_medicine", label: "Family Medicine", icon: "👨‍👩‍👧‍👦" },
  { value: "internal_medicine", label: "Internal Medicine", icon: "💊" },
  { value: "pediatrics", label: "Pediatrics", icon: "👶" },
  { value: "obgyn", label: "OB/GYN", icon: "🤰" },
  { value: "surgery", label: "Surgery", icon: "🔪" },
  { value: "orthopedics", label: "Orthopedics", icon: "🦴" },
  { value: "dermatology", label: "Dermatology", icon: "🧴" },
  { value: "mental_health", label: "Mental Health", icon: "🧠" },
  { value: "cardiology", label: "Cardiology", icon: "❤️" },
  { value: "neurology", label: "Neurology", icon: "🧬" },
  { value: "ent", label: "ENT", icon: "👂" },
  { value: "ophthalmology", label: "Ophthalmology", icon: "👁️" },
  { value: "other", label: "Other", icon: "➕" },
];

export default function BookPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading...</div>}>
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
      // If doctor pre-selected, load all doctors to find their specialty
      fetchDoctors().then((docs) => {
        setDoctors(docs);
        const doc = docs.find((d) => d.id === Number(preselectedDoctor));
        if (doc) {
          setSpecialty(doc.specialty);
          setStep(4); // Skip to issue description
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
      alert("Please open this app from Telegram.");
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
      alert("Failed to book session. Please try again.");
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
            {isPaid ? "Payment Required" : "Session Requested!"}
          </h3>
          {isPaid ? (
            <div className="mb-6">
              <p className="text-ink-secondary text-[14px] max-w-[300px] leading-relaxed mb-4">
                Please transfer <span className="font-bold text-ink-rich">500 ETB</span> to complete your booking.
              </p>
              <div className="card p-4 text-left mb-3">
                <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-2">Bank Details</p>
                <div className="space-y-1.5">
                  <p className="text-[13px] text-ink-body"><span className="text-ink-muted">Bank:</span> Commercial Bank of Ethiopia</p>
                  <p className="text-[13px] text-ink-body"><span className="text-ink-muted">Account:</span> 1000XXXXXXXXX</p>
                  <p className="text-[13px] text-ink-body"><span className="text-ink-muted">Name:</span> LongiMed Health</p>
                </div>
              </div>
              <p className="text-[12px] text-ink-muted leading-relaxed">
                Send your payment receipt to the bot. We&apos;ll confirm within 1 hour.
              </p>
            </div>
          ) : (
            <p className="text-ink-secondary text-[14px] max-w-[280px] leading-relaxed mb-6">
              Awaiting doctor confirmation. You&apos;ll be notified when the session starts.
            </p>
          )}
          <button
            onClick={() => router.push("/sessions")}
            className="bg-brand-teal text-white rounded-2xl px-6 py-3 font-display font-bold text-[14px] hover:bg-brand-teal-deep transition-colors"
          >
            View My Sessions
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="pt-5 pb-8">
      {/* Back */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Link href="/doctors" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back
        </Link>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight mb-1">
          Book Consultation
        </h1>
        <p className="text-ink-secondary text-[14px]">Private session with a verified doctor</p>
      </motion.div>

      {/* Step 1: Package */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="mb-6"
      >
        <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
          Step 1 of 6 — Package
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
                  Free Trial
                </p>
                <p className="text-[12px] text-ink-muted mt-0.5">15-minute session to try the service</p>
              </div>
              <span className="text-[13px] font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-xl">FREE</span>
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
                  Single Session
                </p>
                <p className="text-[12px] text-ink-muted mt-0.5">30-minute full consultation</p>
              </div>
              <span className="text-[13px] font-bold text-brand-gold bg-brand-gold-light px-3 py-1 rounded-xl">500 ETB</span>
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
            Step 2 of 6 — Specialty
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
                  {spec.label}
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
            Step 3 of 6 — Doctor
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
                          Dr. {doc.full_name}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[12px] text-ink-secondary">
                            {doc.rating_avg > 0 ? `★ ${doc.rating_avg}` : "New"}
                          </span>
                          <span className="text-[11px] text-emerald-600 font-semibold">Available</span>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="card p-6 text-center">
              <p className="text-ink-muted text-[13px]">No available doctors in this specialty right now.</p>
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
            Step {preselectedDoctor ? "2 of 4" : "4 of 6"} — Describe Your Issue
          </p>
          <textarea
            value={issueDescription}
            onChange={(e) => setIssueDescription(e.target.value)}
            placeholder="Briefly describe what you need help with..."
            rows={4}
            className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all resize-none"
          />
          {issueDescription.trim().length >= 5 && step < 5 && (
            <button
              onClick={() => setStep(5)}
              className="mt-2 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              Continue →
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
            Step {preselectedDoctor ? "3 of 4" : "5 of 6"} — Privacy
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
                <p className="text-[14px] font-semibold text-ink-rich">Stay anonymous</p>
                <p className="text-[12px] text-ink-muted">Messages relayed through the bot</p>
              </div>
            </button>
          </div>
          {step === 5 && (
            <button
              onClick={() => setStep(6)}
              className="mt-3 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              Continue without anonymous →
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
            Step {preselectedDoctor ? "4 of 4" : "6 of 6"} — Review
          </p>
          <div className="card p-4 mb-4 border-l-4 border-l-brand-teal">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">Package</span>
                <span className="text-[13px] font-semibold text-ink-rich">
                  {pkg === "FREE_TRIAL" ? "Free Trial" : "Single Session (500 ETB)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">Specialty</span>
                <span className="text-[13px] font-semibold text-ink-rich capitalize">{specialty.replace("_", " ")}</span>
              </div>
              {selectedDoctorObj && (
                <div className="flex justify-between">
                  <span className="text-[12px] text-ink-muted">Doctor</span>
                  <span className="text-[13px] font-semibold text-ink-rich">Dr. {selectedDoctorObj.full_name}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">Anonymous</span>
                <span className="text-[13px] font-semibold text-ink-rich">{isAnonymous ? "Yes" : "No"}</span>
              </div>
              {issueDescription && (
                <div className="pt-2 border-t border-surface-border">
                  <span className="text-[12px] text-ink-muted">Issue</span>
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
            {submitting ? "Booking..." : pkg === "SINGLE" ? "Confirm & Pay 500 ETB" : "Confirm Booking"}
          </button>
        </motion.div>
      )}
    </div>
  );
}
