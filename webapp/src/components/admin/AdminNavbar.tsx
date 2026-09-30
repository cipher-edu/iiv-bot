"use client";

import { Bell, Search, ShieldCheck } from "lucide-react";

export function AdminNavbar() {
  return (
    <header className="h-16 px-6 bg-card/80 backdrop-blur-md border-b border-border/70 flex items-center justify-between sticky top-0 z-30">
      {/* Search Input */}
      <div className="relative hidden md:block w-full max-w-xs">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Kurs, xodim yoki audit log qidirish..."
          className="w-full pl-10 pr-4 py-2 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all"
        />
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3.5">
        <button
          className="w-9 h-9 rounded-xl bg-secondary hover:bg-secondary/80 flex items-center justify-center text-muted-foreground hover:text-foreground relative transition-colors"
          title="Bildirishnomalar"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary" />
        </button>

        <div className="hidden sm:flex items-center space-x-3 pl-2 border-l border-border/60">
          <div className="text-right">
            <p className="text-xs font-bold text-foreground">Super Administrator</p>
            <p className="text-[10px] text-muted-foreground">IIV Boshqarma xizmati</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-primary text-primary-foreground font-bold text-xs flex items-center justify-center shadow-sm">
            SA
          </div>
        </div>
      </div>
    </header>
  );
}
