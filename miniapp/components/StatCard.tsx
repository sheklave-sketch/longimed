"use client";

import { motion } from "framer-motion";

export default function StatCard({
  label, value, icon, accent = "teal", index = 0,
}: {
  label: string; value: string | number; icon: string;
  accent?: "teal" | "blue" | "gold" | "rose"; index?: number;
}) {
  const iconBg: Record<string, string> = {
    teal: "bg-brand-teal-light text-brand-teal-deep",
    blue: "bg-brand-blue-light text-brand-blue",
    gold: "bg-brand-gold-light text-brand-gold",
    rose: "bg-pink-50 text-pink-600",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08, ease: [0.16, 1, 0.3, 1] }}
      className={`card stat-bar stat-bar-${accent} p-4`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em]">{label}</p>
          <p className="text-[22px] font-display font-bold text-ink-rich mt-0.5 tracking-tight">{value}</p>
        </div>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-base ${iconBg[accent]}`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
}
