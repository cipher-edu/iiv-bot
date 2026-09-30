"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GraduationCap,
  FileCheck,
  Users,
  Megaphone,
  ShieldAlert,
  Smartphone,
  ShieldCheck,
} from "lucide-react";

const links = [
  { href: "/admin", label: "Statistika", short: "Statistika", icon: LayoutDashboard },
  { href: "/admin/courses", label: "Kurslar Konstruktori", short: "Kurslar", icon: GraduationCap },
  { href: "/admin/tests", label: "Testlar & AI Generator", short: "Testlar", icon: FileCheck },
  { href: "/admin/users", label: "Foydalanuvchilar & Rollar", short: "Odamlar", icon: Users },
  { href: "/admin/broadcast", label: "Ommaviy Xabarnoma", short: "Xabar", icon: Megaphone },
  { href: "/admin/audit", label: "Audit & Xavfsizlik", short: "Audit", icon: ShieldAlert },
];

export function AdminMobileNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-50 bg-card/95 backdrop-blur border-t border-border/70 pb-[env(safe-area-inset-bottom)]">
      <div className="grid grid-cols-6">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive =
            link.href === "/admin" ? pathname === "/admin" : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-semibold ${
                isActive ? "text-primary" : "text-muted-foreground"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="truncate max-w-full px-0.5">{link.short}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 bg-card border-r border-border/70 flex-col justify-between shrink-0 min-h-screen">
      <div>
        {/* Brand Lockup */}
        <div className="h-16 px-6 flex items-center space-x-3 border-b border-border/60">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-extrabold text-sm tracking-tight text-foreground">
              IIV EduBot
            </h1>
            <span className="text-[10px] text-primary font-bold uppercase tracking-wider">
              Admin Platform
            </span>
          </div>
        </div>

        {/* Nav Links */}
        <div className="px-3 py-4 space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive =
              link.href === "/admin"
                ? pathname === "/admin"
                : pathname.startsWith(link.href);

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/70"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Bottom Switcher & Profile */}
      <div className="p-3 border-t border-border/60 space-y-2">
        <Link
          href="/"
          className="flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-primary bg-primary/10 hover:bg-primary/20 transition-colors"
        >
          <Smartphone className="w-4 h-4 shrink-0" />
          <span>Telegram Mini App (User)</span>
        </Link>

        <div className="px-3 py-2 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-foreground">Server: Faol</span>
          </div>
          <span className="text-[10px]">v2.0.0</span>
        </div>
      </div>
    </aside>
  );
}
