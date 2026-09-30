"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, CheckSquare, Trophy, Bot, User } from "lucide-react";
import { triggerHaptic } from "@/lib/telegram";

export function BottomNav() {
  const pathname = usePathname();

  const navItems = [
    { href: "/courses", label: "Kurslar", icon: BookOpen },
    { href: "/tests", label: "Testlar", icon: CheckSquare },
    { href: "/rating", label: "Reyting", icon: Trophy },
    { href: "/ai-tutor", label: "AI Tyutor", icon: Bot },
    { href: "/profile", label: "Profil", icon: User },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-card/90 backdrop-blur-lg border-t border-border/60 pb-[env(safe-area-inset-bottom)] max-w-md mx-auto">
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => triggerHaptic("light")}
              className={`flex flex-col items-center justify-center flex-1 py-1 transition-all duration-200 ${
                isActive
                  ? "text-primary font-medium scale-105"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <div className="relative">
                <Icon className={`w-5 h-5 transition-transform ${isActive ? "stroke-[2.5]" : "stroke-[1.8]"}`} />
                {isActive && (
                  <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-primary rounded-full animate-pulse" />
                )}
              </div>
              <span className="text-[11px] mt-1 tracking-tight">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
