"use client";

import Link from "next/link";
import { Flame, ShieldCheck, Bell } from "lucide-react";
import { useSession } from "@/lib/session";

const STAFF = new Set(["superadmin"]);

export function TopHeader() {
  const { user } = useSession();
  const userName = user.fullName;
  const streak = user.streakDays;

  return (
    <header className="sticky top-0 z-40 bg-card/85 backdrop-blur-md border-b border-border/50 px-4 py-3 max-w-md mx-auto">
      <div className="flex items-center justify-between">
        <Link href="/profile" className="flex items-center space-x-3 group">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-blue-400 p-[2px]">
              <div className="w-full h-full rounded-full bg-background flex items-center justify-center overflow-hidden font-bold text-sm text-primary">
                {userName.charAt(0)}
              </div>
            </div>
            <div className="absolute -bottom-1 -right-1 bg-green-500 w-3.5 h-3.5 rounded-full border-2 border-background" />
          </div>

          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-semibold text-sm tracking-tight text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                {userName}
              </span>
              {STAFF.has(user.role) && (
                <ShieldCheck className="w-4 h-4 text-primary shrink-0" />
              )}
            </div>
            <p className="text-[11px] text-muted-foreground line-clamp-1">
              {user.organization || "IIV Akademiyasi"}
            </p>
          </div>
        </Link>

        <div className="flex items-center space-x-2">
          {/* Streak Badge */}
          <Link
            href="/rating"
            className="flex items-center space-x-1 bg-amber-500/10 border border-amber-500/20 text-amber-500 px-2.5 py-1 rounded-full text-xs font-semibold shadow-sm hover:bg-amber-500/20 transition-colors"
          >
            <Flame className="w-4 h-4 fill-amber-500 text-amber-500 animate-bounce" />
            <span>{streak} kun</span>
          </Link>

          {/* Quick Notification or Admin Shortcut */}
          {STAFF.has(user.role) && (
            <Link
              href="/admin"
              title="Admin panelga o'tish"
              className="w-8 h-8 rounded-full bg-secondary/80 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            >
              <Bell className="w-4 h-4" />
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
