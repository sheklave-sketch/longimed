"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import StatCard from "@/components/StatCard";
import EmptyState from "@/components/EmptyState";
import { initTelegram, getTelegramUser } from "@/lib/telegram";

interface DashboardData {
  doctor: {
    full_name: string;
    specialty: string;
    is_available: boolean;
    rating_avg: number;
    rating_count: number;
  } | null;
  stats: {
    total_sessions: number;
    active_sessions: number;
    pending_queue: number;
    pending_earnings: number;
    paid_earnings: number;
  };
  recent_sessions: Array<{
    id: number;
    status: string;
    issue_description: string;
    created_at: string;
  }>;
}

export default function DoctorDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);

  useEffect(() => {
    initTelegram();
    const user = getTelegramUser();
    const tgId = user?.id || 0;

    fetch(`/api/doctors/dashboard/${tgId}`)
      .then((r) => {
        if (!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const toggleAvailability = async () => {
    if (!data?.doctor) return;
    setToggling(true);
    const user = getTelegramUser();
    try {
      const res = await fetch(`/api/doctors/toggle-availability/${user?.id}`, {
        method: "POST",
      });
      if (res.ok) {
        setData((prev) =>
          prev
            ? {
                ...prev,
                doctor: prev.doctor
                  ? { ...prev.doctor, is_available: !prev.doctor.is_available }
                  : null,
              }
            : null
        );
      }
    } catch {
      // ignore
    } finally {
      setToggling(false);
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

  if (!data?.doctor) {
    return (
      <EmptyState
        icon="🔒"
        title="Doctor Access Only"
        subtitle="This dashboard is for verified LongiMed doctors. Register through the bot to get started."
      />
    );
  }

  const { doctor, stats, recent_sessions } = data;

  return (
    <div className="pt-4 pb-8">
      {/* Welcome */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-5"
      >
        <h1 className="font-display font-bold text-2xl text-navy-600">
          Dr. {doctor.full_name}
        </h1>
        <p className="text-navy-300 text-sm mt-0.5">
          {doctor.specialty.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())} Specialist
        </p>
      </motion.div>

      {/* Availability toggle */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="glass rounded-2xl p-4 shadow-glass mb-4 flex items-center justify-between"
      >
        <div>
          <p className="font-display font-semibold text-navy-600 text-sm">Availability</p>
          <p className={`text-xs mt-0.5 ${doctor.is_available ? "text-emerald-500" : "text-red-400"}`}>
            {doctor.is_available ? "Accepting patients" : "Not accepting patients"}
          </p>
        </div>
        <button
          onClick={toggleAvailability}
          disabled={toggling}
          className={`
            relative w-14 h-7 rounded-full transition-all duration-300
            ${doctor.is_available ? "bg-emerald-400" : "bg-navy-200"}
            ${toggling ? "opacity-50" : ""}
          `}
        >
          <span
            className={`
              absolute top-0.5 w-6 h-6 rounded-full bg-white shadow-sm transition-all duration-300
              ${doctor.is_available ? "left-7" : "left-0.5"}
            `}
          />
        </button>
      </motion.div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <StatCard label="Sessions" value={stats.total_sessions} icon="🩺" accent="teal" index={0} />
        <StatCard label="In Queue" value={stats.pending_queue} icon="📋" accent="blue" index={1} />
        <StatCard label="Rating" value={`${doctor.rating_avg}/5`} icon="⭐" accent="amber" index={2} />
        <StatCard label="Active" value={stats.active_sessions} icon="💬" accent="rose" index={3} />
      </div>

      {/* Earnings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="glass rounded-2xl p-5 shadow-glass mb-5"
      >
        <h2 className="font-display font-semibold text-navy-500 text-sm mb-3">
          Earnings
        </h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-navy-300 uppercase tracking-wider">Pending</p>
            <p className="font-display font-bold text-xl text-amber-500">
              {stats.pending_earnings.toLocaleString()} ETB
            </p>
          </div>
          <div className="w-px h-10 bg-navy-100" />
          <div>
            <p className="text-xs text-navy-300 uppercase tracking-wider">Paid</p>
            <p className="font-display font-bold text-xl text-emerald-500">
              {stats.paid_earnings.toLocaleString()} ETB
            </p>
          </div>
        </div>
      </motion.div>

      {/* Recent sessions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <h2 className="font-display font-semibold text-navy-500 text-sm mb-3">
          Recent Sessions
        </h2>
        {recent_sessions.length > 0 ? (
          <div className="space-y-2">
            {recent_sessions.map((s) => {
              const statusColors: Record<string, string> = {
                active: "bg-emerald-50 text-emerald-600",
                resolved: "bg-navy-50 text-navy-400",
                awaiting_doctor: "bg-amber-50 text-amber-600",
                cancelled: "bg-red-50 text-red-400",
              };
              return (
                <div
                  key={s.id}
                  className="glass rounded-xl p-3 shadow-glass flex items-center gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-navy-600 truncate">
                      {s.issue_description.slice(0, 60)}...
                    </p>
                    <p className="text-xs text-navy-200 mt-0.5">
                      {new Date(s.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      statusColors[s.status] || "bg-navy-50 text-navy-400"
                    }`}
                  >
                    {s.status.replace("_", " ")}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="glass rounded-xl p-6 text-center shadow-glass">
            <p className="text-navy-200 text-sm">No sessions yet</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
