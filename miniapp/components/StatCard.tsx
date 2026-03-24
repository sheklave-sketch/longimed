"use client";

import { motion } from "framer-motion";

export default function StatCard({
  label,
  value,
  icon,
  accent = "teal",
  index = 0,
}: {
  label: string;
  value: string | number;
  icon: string;
  accent?: "teal" | "blue" | "amber" | "rose";
  index?: number;
}) {
  const accentMap = {
    teal: "from-teal-400 to-teal-500",
    blue: "from-sky-400 to-blue-500",
    amber: "from-amber-400 to-orange-500",
    rose: "from-rose-400 to-pink-500",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      className="stat-card glass rounded-2xl p-4 shadow-glass"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-navy-300 font-medium uppercase tracking-wider">
            {label}
          </p>
          <p className="text-2xl font-display font-bold text-navy-600 mt-1">
            {value}
          </p>
        </div>
        <div
          className={`w-10 h-10 rounded-xl bg-gradient-to-br ${accentMap[accent]} flex items-center justify-center text-lg shadow-sm`}
        >
          {icon}
        </div>
      </div>
    </motion.div>
  );
}
