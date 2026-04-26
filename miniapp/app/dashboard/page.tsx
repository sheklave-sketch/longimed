"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import DoctorProfileEditor, { DoctorProfile } from "@/components/DoctorProfileEditor";
import { initTelegram, getTelegramUser } from "@/lib/telegram";

interface DashboardData {
  doctor: (DoctorProfile & { is_available: boolean; rating_avg: number; rating_count: number }) | null;
  stats: { total_sessions: number; active_sessions: number; pending_queue: number; pending_earnings: number; paid_earnings: number };
  recent_sessions: Array<{ id: number; status: string; issue_description: string; created_at: string }>;
}

export default function DoctorDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);

  useEffect(() => {
    initTelegram();
    const tgId = getTelegramUser()?.id || 0;
    fetch(`/api/doctors/dashboard/${tgId}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const toggle = async () => {
    if (!data?.doctor) return;
    setToggling(true);
    try {
      const res = await fetch(`/api/doctors/toggle-availability/${getTelegramUser()?.id}`, { method: "POST" });
      if (res.ok) setData((p) => p ? { ...p, doctor: p.doctor ? { ...p.doctor, is_available: !p.doctor.is_available } : null } : null);
    } catch {} finally { setToggling(false); }
  };

  if (loading) return (
    <div className="pt-6 space-y-3">
      {[1, 2, 3, 4].map((i) => <div key={i} className="card p-4 h-20"><div className="skeleton h-full rounded-lg" /></div>)}
    </div>
  );

  if (!data?.doctor) {
    if (typeof window !== "undefined") window.location.href = "/";
    return null;
  }

  const { doctor, stats, recent_sessions } = data;
  const specLabel = doctor.specialty.replace("_", " ").replace(/\b\w/g, (c: string) => c.toUpperCase());
  const totalEarnings = stats.pending_earnings + stats.paid_earnings;
  const paidPercent = totalEarnings > 0 ? Math.round((stats.paid_earnings / totalEarnings) * 100) : 0;

  return (
    <div className="pt-5 pb-8">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-5">
        <p className="text-[12px] font-semibold text-ink-muted uppercase tracking-[0.1em] mb-1">Dashboard</p>
        <h1 className="font-display font-bold text-[24px] text-ink-rich tracking-tight">Dr. {doctor.full_name}</h1>
        <p className="text-ink-secondary text-[13px] mt-0.5">{specLabel} Specialist</p>
      </motion.div>

      {/* Availability */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
        className="card p-4 mb-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${doctor.is_available ? "status-online" : "status-offline"}`} />
          <div>
            <p className="font-display font-semibold text-ink-rich text-[14px]">
              {doctor.is_available ? "Available" : "Unavailable"}
            </p>
            <p className="text-[11px] text-ink-muted">
              {doctor.is_available ? "Accepting new patients" : "Not accepting patients"}
            </p>
          </div>
        </div>
        <button onClick={toggle} disabled={toggling}
          className={`relative w-12 h-[26px] rounded-full transition-all duration-300 ${doctor.is_available ? "bg-brand-teal" : "bg-surface-border"} ${toggling ? "opacity-50" : ""}`}
        >
          <span className={`absolute top-[3px] w-5 h-5 rounded-full bg-white shadow-sm transition-all duration-300 ${doctor.is_available ? "left-[25px]" : "left-[3px]"}`} />
        </button>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <StatCard label="Sessions" value={stats.total_sessions} icon="🩺" accent="teal" index={0} />
        <StatCard label="In Queue" value={stats.pending_queue} icon="📋" accent="blue" index={1} />
        <StatCard label="Rating" value={`${doctor.rating_avg}/5`} icon="⭐" accent="gold" index={2} />
        <StatCard label="Active" value={stats.active_sessions} icon="💬" accent="rose" index={3} />
      </div>

      {/* Earnings */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card p-5 mb-5">
        <h2 className="font-display font-semibold text-ink-rich text-[14px] mb-4">Earnings</h2>
        {/* Progress bar */}
        <div className="h-2 bg-surface-muted rounded-full overflow-hidden mb-4">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${paidPercent}%` }}
            transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="h-full bg-gradient-teal rounded-full"
          />
        </div>
        <div className="flex justify-between">
          <div>
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">Pending</p>
            <p className="font-display font-bold text-[20px] text-brand-gold tracking-tight">{stats.pending_earnings.toLocaleString()} <span className="text-[12px] font-medium text-ink-muted">ETB</span></p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">Paid</p>
            <p className="font-display font-bold text-[20px] text-emerald-600 tracking-tight">{stats.paid_earnings.toLocaleString()} <span className="text-[12px] font-medium text-ink-muted">ETB</span></p>
          </div>
        </div>
      </motion.div>

      {/* Profile editor */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.32 }} className="mb-5">
        <details className="card overflow-hidden group">
          <summary className="p-5 flex items-center justify-between cursor-pointer list-none">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-brand-teal-light flex items-center justify-center text-[16px]">✏️</div>
              <div>
                <h2 className="font-display font-semibold text-ink-rich text-[14px]">Your profile</h2>
                <p className="text-[11px] text-ink-muted mt-0.5">Bio, photo, languages — what patients see</p>
              </div>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-ink-muted transition-transform group-open:rotate-180"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
          </summary>
          <div className="px-5 pb-5 pt-2 border-t border-surface-border">
            <DoctorProfileEditor
              initial={doctor}
              endpoint={`/api/doctors/${getTelegramUser()?.id || 0}/profile`}
              onSaved={(updated) => setData((p) => p && p.doctor ? { ...p, doctor: { ...p.doctor, ...updated } } : p)}
            />
          </div>
        </details>
      </motion.div>

      {/* Recent sessions */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
        <h2 className="font-display font-semibold text-ink-rich text-[14px] mb-3">Recent Sessions</h2>
        {recent_sessions.length > 0 ? (
          <div className="space-y-2">
            {recent_sessions.map((s) => {
              const sc: Record<string, string> = {
                active: "bg-emerald-50 text-emerald-700 border-emerald-200",
                resolved: "bg-surface-muted text-ink-muted border-surface-border",
                awaiting_doctor: "bg-amber-50 text-amber-700 border-amber-200",
                cancelled: "bg-red-50 text-red-500 border-red-200",
              };
              return (
                <div key={s.id} className="card p-3.5 flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] text-ink-rich truncate font-medium">{s.issue_description.slice(0, 55)}...</p>
                    <p className="text-[11px] text-ink-muted mt-0.5">{new Date(s.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`shrink-0 px-2 py-[3px] rounded-lg border text-[10px] font-semibold ${sc[s.status] || sc.resolved}`}>
                    {s.status.replace("_", " ")}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center"><p className="text-ink-muted text-[13px]">No sessions yet</p></div>
        )}
      </motion.div>
    </div>
  );
}
