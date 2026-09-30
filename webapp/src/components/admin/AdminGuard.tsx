"use client";

import Link from "next/link";
import { useSession } from "@/lib/session";
import { AdminNavbar } from "@/components/admin/AdminNavbar";
import { AdminMobileNav, AdminSidebar } from "@/components/admin/AdminSidebar";

const STAFF = new Set(["superadmin"]);

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user } = useSession();
  if (!STAFF.has(user.role)) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="max-w-lg w-full bg-card border border-border/70 rounded-3xl p-8 text-center space-y-3">
          <h1 className="text-lg font-black text-foreground">Bu bo&apos;lim yopiq</h1>
          <p className="text-sm text-muted-foreground">
            Boshqaruv paneli faqat superadmin uchun.
          </p>
          <Link href="/" className="inline-block text-sm font-semibold text-primary">
            O&apos;quv sahifasiga qaytish
          </Link>
        </div>
      </div>
    );
  }
  return (
    <div className="flex min-h-screen bg-background">
      <AdminSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <AdminNavbar />
        <main className="flex-1 p-4 pb-24 md:p-8 md:pb-8 overflow-y-auto">{children}</main>
        <AdminMobileNav />
      </div>
    </div>
  );
}
