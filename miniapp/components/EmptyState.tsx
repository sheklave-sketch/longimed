"use client";

import { motion } from "framer-motion";

export default function EmptyState({ icon, title, subtitle }: { icon: string; title: string; subtitle: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center py-20 px-6 text-center"
    >
      <div className="w-16 h-16 rounded-2xl bg-surface-muted flex items-center justify-center text-3xl mb-4">
        {icon}
      </div>
      <h3 className="font-display font-semibold text-ink-rich text-base">{title}</h3>
      <p className="text-ink-secondary text-sm mt-1.5 max-w-[260px] leading-relaxed">{subtitle}</p>
    </motion.div>
  );
}
