"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Doctors", icon: "👨‍⚕️" },
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/admin", label: "Admin", icon: "⚙️" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 glass shadow-glass">
      <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/logo-icon.png"
            alt="LongiMed"
            width={32}
            height={32}
            className="rounded-lg"
          />
          <span className="font-display font-bold text-navy-600 text-lg tracking-tight">
            LongiMed
          </span>
        </Link>

        <nav className="flex gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                  ${active
                    ? "bg-teal-400 text-white shadow-glow"
                    : "text-navy-400 hover:text-navy-600 hover:bg-white/60"
                  }
                `}
              >
                <span className="mr-1">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
