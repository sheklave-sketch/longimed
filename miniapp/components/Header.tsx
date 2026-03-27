"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getTelegramUser } from "@/lib/telegram";
import { t } from "@/lib/i18n";

interface UserRole {
  is_doctor: boolean;
  is_admin: boolean;
}

export default function Header() {
  const path = usePathname();
  const [role, setRole] = useState<UserRole>({ is_doctor: false, is_admin: false });

  useEffect(() => {
    const tgId = getTelegramUser()?.id;
    if (tgId) {
      fetch(`/api/user/role/${tgId}`)
        .then((r) => r.ok ? r.json() : { is_doctor: false, is_admin: false })
        .then(setRole)
        .catch(() => {});
    }
  }, []);

  const tabs = [
    { href: "/doctors", label: t("nav_doctors"), show: true },
    { href: "/qa", label: t("nav_qa"), show: true },
    { href: "/book", label: t("nav_book"), show: !role.is_doctor },
    { href: "/dashboard", label: t("nav_dashboard"), show: role.is_doctor },
    { href: "/admin", label: t("nav_admin"), show: role.is_admin },
  ].filter((tab) => tab.show);

  return (
    <header className="sticky top-0 z-40 bg-surface-white/80 backdrop-blur-xl border-b border-surface-border">
      <div className="max-w-lg mx-auto px-4 h-13 flex items-center gap-3">
        <Link href="/" className="shrink-0 flex items-center gap-2">
          <Image src="/logo-icon.png" alt="LongiMed" width={26} height={26} className="rounded-md" />
          <span className="hidden min-[380px]:inline font-display font-bold text-ink-rich text-[15px] tracking-[-0.02em]">
            Longi<span className="text-brand-teal">Med</span>
          </span>
        </Link>

        <nav className="flex-1 flex justify-end">
          <div className="flex bg-surface-muted rounded-xl p-0.5">
            {tabs.map((item) => {
              const active = path.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    px-3 py-1.5 rounded-lg text-[11px] font-semibold tracking-wide transition-all duration-200 whitespace-nowrap
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
          </div>
        </nav>
      </div>
    </header>
  );
}
