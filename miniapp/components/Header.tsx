"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Doctors" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/admin", label: "Admin" },
];

export default function Header() {
  const path = usePathname();

  return (
    <header className="sticky top-0 z-40 bg-surface-white/80 backdrop-blur-xl border-b border-surface-border">
      <div className="max-w-lg mx-auto px-5 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <Image src="/logo-icon.png" alt="LongiMed" width={28} height={28} className="rounded-md" />
          <span className="font-display font-bold text-ink-rich text-[17px] tracking-[-0.02em]">
            Longi<span className="text-brand-teal">Med</span>
          </span>
        </Link>

        <nav className="flex bg-surface-muted rounded-xl p-0.5">
          {NAV.map((item) => {
            const active = item.href === "/" ? path === "/" : path.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  px-3.5 py-1.5 rounded-lg text-[12px] font-semibold tracking-wide transition-all duration-200
                  ${active
                    ? "bg-surface-white text-brand-teal shadow-soft"
                    : "text-ink-muted hover:text-ink-body"
                  }
                `}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
