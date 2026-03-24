"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import { initTelegram, getTelegramUser } from "@/lib/telegram";

interface AdminData {
  stats: { total_users: number; total_doctors: number; total_questions: number; total_sessions: number; pending_doctors: number; pending_questions: number };
  pending_doctors: Array<{ id: number; full_name: string; specialty: string; license_number: string; applied_at: string }>;
  recent_payments: Array<{ id: number; amount_etb: number; status: string; created_at: string; user_telegram_id: number }>;
}

export default function AdminPanel() {
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    initTelegram();
    const tgId = getTelegramUser()?.id || 0;
    fetch(`/api/admin/dashboard/${tgId}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const handleAction = async (id: number, action: "approve" | "reject") => {
    setActionLoading(id);
    try {
      const res = await fetch(`/api/admin/doctors/${id}/${action}`, { method: "POST" });
      if (res.ok) setData((p) => p ? {
        ...p, pending_doctors: p.pending_doctors.filter((d) => d.id !== id),
        stats: { ...p.stats, pending_doctors: p.stats.pending_doctors - 1, total_doctors: action === "approve" ? p.stats.total_doctors + 1 : p.stats.total_doctors },
      } : null);
    } catch {} finally { setActionLoading(null); }
  };

  if (loading) return (
    <div className="pt-6 space-y-3">
      {[1, 2, 3, 4].map((i) => <div key={i} className="card p-4 h-20"><div className="skeleton h-full rounded-lg" /></div>)}
    </div>
  );

  if (!data) return <EmptyState icon="🔒" title="Admin Access Only" subtitle="You don't have permission to view this page." />;

  const { stats, pending_doctors, recent_payments } = data;

  return (
    <div className="pt-5 pb-8">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-5">
        <p className="text-[12px] font-semibold text-ink-muted uppercase tracking-[0.1em] mb-1">Admin</p>
        <h1 className="font-display font-bold text-[24px] text-ink-rich tracking-tight">Platform Overview</h1>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <StatCard label="Users" value={stats.total_users} icon="👥" accent="teal" index={0} />
        <StatCard label="Doctors" value={stats.total_doctors} icon="👨‍⚕️" accent="blue" index={1} />
        <StatCard label="Questions" value={stats.total_questions} icon="❓" accent="gold" index={2} />
        <StatCard label="Sessions" value={stats.total_sessions} icon="🩺" accent="rose" index={3} />
      </div>

      {/* Pending alert */}
      {(stats.pending_doctors > 0 || stats.pending_questions > 0) && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="card p-4 mb-5 border-l-[3px] border-l-brand-gold"
        >
          <p className="font-display font-semibold text-ink-rich text-[13px] mb-1.5">Action Required</p>
          <div className="space-y-1">
            {stats.pending_doctors > 0 && (
              <p className="text-[12px] text-ink-body"><span className="font-bold text-brand-gold">{stats.pending_doctors}</span> doctor application{stats.pending_doctors > 1 ? "s" : ""} pending</p>
            )}
            {stats.pending_questions > 0 && (
              <p className="text-[12px] text-ink-body"><span className="font-bold text-brand-gold">{stats.pending_questions}</span> question{stats.pending_questions > 1 ? "s" : ""} awaiting review</p>
            )}
          </div>
        </motion.div>
      )}

      {/* Doctor applications */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="mb-6">
        <h2 className="font-display font-semibold text-ink-rich text-[14px] mb-3">Doctor Applications</h2>
        {pending_doctors.length > 0 ? (
          <div className="space-y-3">
            {pending_doctors.map((doc) => (
              <div key={doc.id} className="card p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-teal-soft flex items-center justify-center font-display font-bold text-brand-teal-deep text-[14px]">
                      {doc.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </div>
                    <div>
                      <p className="font-display font-semibold text-ink-rich text-[14px]">Dr. {doc.full_name}</p>
                      <p className="text-[11px] text-ink-secondary">{doc.specialty.replace("_", " ")} · <span className="font-mono">{doc.license_number}</span></p>
                    </div>
                  </div>
                  <span className="text-[10px] text-ink-muted bg-surface-muted px-2 py-0.5 rounded-md">{doc.applied_at ? new Date(doc.applied_at).toLocaleDateString() : "—"}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleAction(doc.id, "approve")} disabled={actionLoading === doc.id}
                    className="flex-1 py-2.5 rounded-xl bg-brand-teal text-white text-[12px] font-bold hover:bg-brand-teal-deep transition-colors disabled:opacity-50 shadow-glow-sm"
                  >Approve</button>
                  <button onClick={() => handleAction(doc.id, "reject")} disabled={actionLoading === doc.id}
                    className="flex-1 py-2.5 rounded-xl bg-surface-muted text-ink-secondary text-[12px] font-bold hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
                  >Reject</button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center"><p className="text-ink-muted text-[13px]">No pending applications</p></div>
        )}
      </motion.div>

      {/* Payments */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <h2 className="font-display font-semibold text-ink-rich text-[14px] mb-3">Recent Payments</h2>
        {recent_payments.length > 0 ? (
          <div className="space-y-2">
            {recent_payments.map((p) => {
              const sc: Record<string, string> = { completed: "bg-emerald-50 text-emerald-700 border-emerald-200", pending: "bg-amber-50 text-amber-700 border-amber-200", failed: "bg-red-50 text-red-500 border-red-200" };
              return (
                <div key={p.id} className="card p-3.5 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-surface-muted flex items-center justify-center text-[14px]">💰</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-ink-rich">{p.amount_etb?.toLocaleString() || "—"} ETB</p>
                    <p className="text-[11px] text-ink-muted">{new Date(p.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`shrink-0 px-2 py-[3px] rounded-lg border text-[10px] font-semibold ${sc[p.status] || sc.pending}`}>{p.status}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center"><p className="text-ink-muted text-[13px]">No payments yet</p></div>
        )}
      </motion.div>
    </div>
  );
}
