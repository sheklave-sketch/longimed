"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { initTelegram, getTelegramUser } from "@/lib/telegram";
import { registerDoctor } from "@/lib/api";

const SPECIALTIES = [
  { value: "general", label: "General Medicine", icon: "🩺" },
  { value: "pediatrics", label: "Pediatrics", icon: "👶" },
  { value: "obgyn", label: "OB/GYN", icon: "🤰" },
  { value: "dermatology", label: "Dermatology", icon: "🧴" },
  { value: "mental_health", label: "Mental Health", icon: "🧠" },
  { value: "cardiology", label: "Cardiology", icon: "❤️" },
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "am", label: "Amharic" },
];

export default function DoctorRegistration() {
  const [step, setStep] = useState(1);
  const [fullName, setFullName] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [languages, setLanguages] = useState<string[]>([]);
  const [bio, setBio] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    initTelegram();
  }, []);

  const toggleLanguage = (lang: string) => {
    setLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const handleSubmit = async () => {
    const tgId = getTelegramUser()?.id;
    if (!tgId) {
      alert("Please open this app from Telegram.");
      return;
    }
    setSubmitting(true);
    try {
      await registerDoctor({
        telegram_id: tgId,
        full_name: fullName.trim(),
        license_number: licenseNumber.trim(),
        specialty,
        languages,
        bio: bio.trim(),
      });
      setSuccess(true);
    } catch {
      alert("Failed to submit registration. Please try again.");
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
            🎉
          </div>
          <h3 className="font-display font-bold text-ink-rich text-lg mb-1.5">Application Submitted!</h3>
          <p className="text-ink-secondary text-[14px] max-w-[300px] leading-relaxed mb-6">
            We&apos;ll review your application within 48 hours. You&apos;ll receive a notification once approved.
          </p>
          <Link
            href="/"
            className="bg-brand-teal text-white rounded-2xl px-6 py-3 font-display font-bold text-[14px] hover:bg-brand-teal-deep transition-colors inline-block"
          >
            Back to Home
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="pt-5 pb-8">
      {/* Back */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Link href="/" className="inline-flex items-center gap-1.5 text-[13px] text-ink-secondary hover:text-brand-teal transition-colors mb-5">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back
        </Link>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6">
        <h1 className="font-display font-bold text-[26px] text-ink-rich tracking-tight leading-tight mb-1">
          Doctor Registration
        </h1>
        <p className="text-ink-secondary text-[14px]">Join our network of verified physicians</p>
      </motion.div>

      {/* Step 1: Full Name */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="mb-6"
      >
        <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
          Step 1 of 6 — Full Name
        </p>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Enter your full name"
          className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all"
        />
        {fullName.trim().length >= 2 && step < 2 && (
          <button
            onClick={() => setStep(2)}
            className="mt-2 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
          >
            Continue →
          </button>
        )}
      </motion.div>

      {/* Step 2: License Number */}
      {step >= 2 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 2 of 6 — License Number
          </p>
          <input
            type="text"
            value={licenseNumber}
            onChange={(e) => setLicenseNumber(e.target.value)}
            placeholder="e.g., FMHACA-12345"
            className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all"
          />
          <p className="text-[11px] text-ink-muted mt-1.5">Your FMHACA medical license number</p>
          {licenseNumber.trim().length >= 3 && step < 3 && (
            <button
              onClick={() => setStep(3)}
              className="mt-2 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              Continue →
            </button>
          )}
        </motion.div>
      )}

      {/* Step 3: Specialty */}
      {step >= 3 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 3 of 6 — Specialty
          </p>
          <div className="grid grid-cols-2 gap-2">
            {SPECIALTIES.map((spec) => (
              <button
                key={spec.value}
                onClick={() => { setSpecialty(spec.value); if (step < 4) setStep(4); }}
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

      {/* Step 4: Languages */}
      {step >= 4 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 4 of 6 — Languages
          </p>
          <div className="space-y-2">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.value}
                onClick={() => toggleLanguage(lang.value)}
                className="card p-4 w-full text-left flex items-center gap-3 transition-all"
              >
                <div className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all shrink-0 ${
                  languages.includes(lang.value) ? "bg-brand-teal border-brand-teal" : "border-surface-border-strong"
                }`}>
                  {languages.includes(lang.value) && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2.5 6L5 8.5L9.5 3.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  )}
                </div>
                <span className="text-[14px] font-semibold text-ink-rich">{lang.label}</span>
              </button>
            ))}
          </div>
          {languages.length > 0 && step < 5 && (
            <button
              onClick={() => setStep(5)}
              className="mt-3 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              Continue →
            </button>
          )}
        </motion.div>
      )}

      {/* Step 5: Bio */}
      {step >= 5 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-3">
            Step 5 of 6 — Bio
          </p>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Tell patients about your experience, education, and areas of focus..."
            rows={4}
            className="w-full bg-surface-white border border-surface-border rounded-2xl px-4 py-3 text-[14px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/10 transition-all resize-none"
          />
          {bio.trim().length >= 10 && step < 6 && (
            <button
              onClick={() => setStep(6)}
              className="mt-2 text-[13px] text-brand-teal font-semibold hover:text-brand-teal-deep transition-colors"
            >
              Review →
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
            Step 6 of 6 — Review
          </p>
          <div className="card p-4 mb-4 border-l-4 border-l-brand-teal">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">Name</span>
                <span className="text-[13px] font-semibold text-ink-rich">{fullName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">License</span>
                <span className="text-[13px] font-semibold text-ink-rich">{licenseNumber}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">Specialty</span>
                <span className="text-[13px] font-semibold text-ink-rich capitalize">{specialty.replace("_", " ")}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[12px] text-ink-muted">Languages</span>
                <span className="text-[13px] font-semibold text-ink-rich">
                  {languages.map((l) => l === "en" ? "English" : "Amharic").join(", ")}
                </span>
              </div>
              {bio && (
                <div className="pt-2 border-t border-surface-border">
                  <span className="text-[12px] text-ink-muted">Bio</span>
                  <p className="text-[13px] text-ink-body mt-0.5 leading-relaxed">{bio}</p>
                </div>
              )}
            </div>
          </div>

          <p className="text-[12px] text-ink-muted mb-4 leading-relaxed">
            Note: License document upload is handled through the Telegram bot. You can send it after registration.
          </p>

          <button
            onClick={handleSubmit}
            disabled={submitting || !fullName.trim() || !licenseNumber.trim() || !specialty || languages.length === 0}
            className="w-full bg-brand-teal text-white rounded-2xl py-3.5 font-display font-bold text-[15px] hover:bg-brand-teal-deep transition-colors disabled:opacity-50 shadow-glow"
          >
            {submitting ? "Submitting..." : "Submit Application"}
          </button>
        </motion.div>
      )}
    </div>
  );
}
