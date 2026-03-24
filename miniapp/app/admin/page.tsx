"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import { initTelegram, getTelegramUser } from "@/lib/telegram";

interface AdminData {
  stats: {
    total_users: number;
    total_doctors: number;
    total_questions: number;
    total_sessions: number;
    pending_doctors: number;
    pending_questions: number;
  };
  pending_doctors: Array<{
    id: number;
    full_name: string;
    specialty: string;
    license_number: string;
    applied_at: string;
  }>;
  recent_payments: Array<{
    id: number;
    amount_etb: number;
    status: string;
    created_at: string;
    user_telegram_id: number;
  }>;
}

export default function AdminPanel() {
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    initTelegram();
    const user = getTelegramUser();
    const tgId = user?.id || 0;

    fetch(`/api/admin/dashboard/${tgId}`)
      .then((r) => {
        if (!r.ok) throw new Error("Unauthorized");
        return r.json();
      })
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const handleDoctorAction = async (doctorId: number, action: "approve" | "reject") => {
    setActionLoading(doctorId);
    try {
      const res = await fetch(`/api/admin/doctors/${doctorId}/${action}`, {
        method: "POST",
      });
      if (res.ok) {
        setData((prev) =>
          prev
            ? {
                ...prev,
                pending_doctors: prev.pending_doctors.filter((d) => d.id !== doctorId),
                stats: {
                  ...prev.stats,
                  pending_doctors: prev.stats.pending_doctors - 1,
                  total_doctors:
                    action === "approve"
                      ? prev.stats.total_doctors + 1
                      : prev.stats.total_doctors,
                },
              }
            : null
        );
      }
    } catch {
      // ignore
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="pt-6 space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass rounded-2xl p-4 h-20 animate-pulse shadow-glass" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <EmptyState
        icon="🔒"
        title="Admin Access Only"
        subtitle="You don't have permission to view this page."
      />
    );
  }

  const { stats, pending_doctors, recent_payments } = data;

  return (
    <div className="pt-4 pb-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-5"
      >
        <h1 className="font-display font-bold text-2xl text-navy-600">
          Admin Panel
        </h1>
        <p className="text-navy-300 text-sm mt-0.5">
          Platform overview and management
        </p>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <StatCard label="Users" value={stats.total_users} icon="👥" accent="teal" index={0} />
        <StatCard label="Doctors" value={stats.total_doctors} icon="👨‍⚕️" accent="blue" index={1} />
        <StatCard label="Questions" value={stats.total_questions} icon="❓" accent="amber" index={2} />
        <StatCard label="Sessions" value={stats.total_sessions} icon="🩺" accent="rose" index={3} />
      </div>

      {/* Pending alerts */}
      {(stats.pending_doctors > 0 || stats.pending_questions > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-2xl p-4 shadow-glass mb-5 border-l-4 border-amber-400"
        >
          <h3 className="font-display font-semibold text-navy-600 text-sm mb-2">
            ⚠️ Pending Actions
          </h3>
          <div className="space-y-1 text-sm">
            {stats.pending_doctors > 0 && (
              <p className="text-navy-400">
                <span className="font-semibold text-amber-500">{stats.pending_doctors}</span> doctor
                {stats.pending_doctors !== 1 ? "s" : ""} awaiting verification
              </p>
            )}
            {stats.pending_questions > 0 && (
              <p className="text-navy-400">
                <span className="font-semibold text-amber-500">{stats.pending_questions}</span> question
                {stats.pending_questions !== 1 ? "s" : ""} awaiting moderation
              </p>
            )}
          </div>
        </motion.div>
      )}

      {/* Pending doctors */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="mb-5"
      >
        <h2 className="font-display font-semibold text-navy-500 text-sm mb-3">
          Doctor Applications
        </h2>
        {pending_doctors.length > 0 ? (
          <div className="space-y-2">
            {pending_doctors.map((doc) => (
              <div
                key={doc.id}
                className="glass rounded-xl p-4 shadow-glass"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-display font-semibold text-navy-600 text-sm">
                      Dr. {doc.full_name}
                    </p>
                    <p className="text-xs text-navy-300">
                      {doc.specialty.replace("_", " ")} · {doc.license_number}
                    </p>
                  </div>
                  <span className="text-[10px] text-navy-200">
                    {new Date(doc.applied_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDoctorAction(doc.id, "approve")}
                    disabled={actionLoading === doc.id}
                    className="flex-1 py-2 rounded-lg bg-emerald-50 text-emerald-600 text-xs font-medium hover:bg-emerald-100 transition-colors disabled:opacity-50"
                  >
                    ✅ Approve
                  </button>
                  <button
                    onClick={() => handleDoctorAction(doc.id, "reject")}
                    disabled={actionLoading === doc.id}
                    className="flex-1 py-2 rounded-lg bg-red-50 text-red-500 text-xs font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                  >
                    ❌ Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass rounded-xl p-6 text-center shadow-glass">
            <p className="text-navy-200 text-sm">No pending applications</p>
          </div>
        )}
      </motion.div>

      {/* Recent payments */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="font-display font-semibold text-navy-500 text-sm mb-3">
          Recent Payments
        </h2>
        {recent_payments.length > 0 ? (
          <div className="space-y-2">
            {recent_payments.map((p) => {
              const statusColors: Record<string, string> = {
                completed: "bg-emerald-50 text-emerald-600",
                pending: "bg-amber-50 text-amber-600",
                failed: "bg-red-50 text-red-400",
              };
              return (
                <div
                  key={p.id}
                  className="glass rounded-xl p-3 shadow-glass flex items-center gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-navy-600">
                      {p.amount_etb?.toLocaleString() || "—"} ETB
                    </p>
                    <p className="text-xs text-navy-200 mt-0.5">
                      {new Date(p.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      statusColors[p.status] || "bg-navy-50 text-navy-400"
                    }`}
                  >
                    {p.status}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="glass rounded-xl p-6 text-center shadow-glass">
            <p className="text-navy-200 text-sm">No payments yet</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
