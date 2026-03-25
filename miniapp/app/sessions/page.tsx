"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import { initTelegram, getTelegramUser } from "@/lib/telegram";
import { fetchMySessions } from "@/lib/api";
import type { SessionItem } from "@/lib/api";

const STATUS_STYLES: Record<string, { bg: string; border: string; text: string; label: string }> = {
  ACTIVE: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", label: "Active" },
  RESOLVED: { bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-600", label: "Resolved" },
  AWAITING_DOCTOR: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", label: "Awaiting" },
  PENDING_APPROVAL: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", label: "Pending" },
  APPROVED: { bg: "bg-brand-blue-light", border: "border-blue-200", text: "text-brand-blue", label: "Approved" },
  CANCELLED: { bg: "bg-red-50", border: "border-red-200", text: "text-red-600", label: "Cancelled" },
  EXPIRED: { bg: "bg-red-50", border: "border-red-200", text: "text-red-600", label: "Expired" },
};

export default function MySessions() {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initTelegram();
    const tgId = getTelegramUser()?.id;
    if (tgId) {
      fetchMySessions(tgId)
        .then(setSessions)
        .catch(() => setSessions([]))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

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
          My Sessions
        </h1>
        <p className="text-ink-secondary text-[14px]">Your consultation history</p>
      </motion.div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-4">
              <div className="space-y-2.5">
                <div className="flex justify-between">
                  <div className="h-4 skeleton w-1/3" />
                  <div className="h-4 skeleton w-16" />
                </div>
                <div className="h-3 skeleton w-full" />
                <div className="h-3 skeleton w-2/3" />
              </div>
            </div>
          ))}
        </div>
      ) : sessions.length > 0 ? (
        <div className="space-y-3">
          {sessions.map((session, i) => {
            const statusStyle = STATUS_STYLES[session.status] || STATUS_STYLES.PENDING_APPROVAL;
            return (
              <motion.div
                key={session.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                className="card p-4"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex px-2 py-[2px] rounded-lg text-[10px] font-semibold border ${statusStyle.bg} ${statusStyle.border} ${statusStyle.text}`}>
                      {statusStyle.label}
                    </span>
                    <span className="text-[11px] text-ink-muted bg-surface-muted px-2 py-0.5 rounded-lg capitalize">
                      {session.package === "FREE_TRIAL" ? "Free" : session.package.toLowerCase().replace("_", " ")}
                    </span>
                  </div>
                  {session.rating && (
                    <span className="text-[12px] text-brand-gold font-semibold">
                      ★ {session.rating}
                    </span>
                  )}
                </div>

                {session.doctor_name && (
                  <p className="text-[14px] font-semibold text-ink-rich mb-1">
                    Dr. {session.doctor_name}
                  </p>
                )}

                <p className="text-ink-secondary text-[13px] leading-relaxed line-clamp-2">
                  {session.issue_description}
                </p>

                <div className="flex items-center gap-3 mt-3">
                  <span className="text-[11px] text-ink-muted">
                    {new Date(session.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                  </span>
                  {session.is_anonymous && (
                    <span className="text-[10px] text-ink-muted bg-surface-muted px-1.5 py-0.5 rounded">Anonymous</span>
                  )}
                  <span className="text-[11px] text-ink-muted capitalize">
                    {session.session_mode.toLowerCase()}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon="📋"
          title="No sessions yet"
          subtitle="Book a consultation with a doctor to get started"
        />
      )}

      {!loading && sessions.length > 0 && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="text-center text-[11px] text-ink-muted mt-5">
          {sessions.length} sessions
        </motion.p>
      )}
    </div>
  );
}
