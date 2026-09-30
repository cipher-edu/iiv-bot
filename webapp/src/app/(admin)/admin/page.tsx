"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Users, GraduationCap, CheckCircle, TrendingUp, AlertTriangle, ArrowUpRight } from "lucide-react";
import { Course } from "@/types";
import { api } from "@/lib/api";

interface Overview {
  usersTotal: number;
  activeToday: number;
  completionRate: number;
  avgScore: number;
  courses: Course[];
  recentUsers: { id: number; name: string; role: string; org: string; date: string }[];
  dropoff: { title: string; note: string }[];
}

export default function AdminDashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);

  useEffect(() => {
    api<Overview>("/api/v1/admin/overview").then(setOverview).catch(() => setOverview(null));
  }, []);

  const kpiStats = [
    { title: "Jami foydalanuvchilar", value: String(overview?.usersTotal ?? "—"), change: "bazadagi hisoblar", isPositive: true, icon: Users, color: "text-blue-500", bg: "bg-blue-500/10" },
    { title: "Faol o'quvchilar (Bugun)", value: String(overview?.activeToday ?? "—"), change: "bugun kirganlar", isPositive: true, icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    { title: "Kurs yakunlash ko'rsatkichi", value: overview ? `${overview.completionRate}%` : "—", change: "yakunlangan yozilishlar", isPositive: true, icon: GraduationCap, color: "text-purple-500", bg: "bg-purple-500/10" },
    { title: "O'rtacha test natijasi", value: overview ? `${overview.avgScore}%` : "—", change: "saqlangan natijalar", isPositive: true, icon: CheckCircle, color: "text-amber-500", bg: "bg-amber-500/10" },
  ];

  const recentRegistrations = overview?.recentUsers || [];
  const courses = overview?.courses || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            Boshqaruv Paneli & Tizim Tahlili
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            IIV EduBot ta&apos;lim platformasi bo&apos;yicha umumiy holat va o&apos;quv jarayoni metrikalari
          </p>
        </div>

        <Link
          href="/admin/courses/new"
          className="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold shadow-md transition-all flex items-center space-x-1.5"
        >
          <span>+ Yangi kurs yaratish</span>
        </Link>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpiStats.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">
                  {kpi.title}
                </span>
                <div className={`w-9 h-9 rounded-xl ${kpi.bg} ${kpi.color} flex items-center justify-center`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>

              <div>
                <h3 className="text-2xl font-black text-foreground tracking-tight">
                  {kpi.value}
                </h3>
                <span className="text-xs font-medium text-emerald-500 mt-1 inline-flex items-center">
                  <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                  {kpi.change}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Course Performance & Drop-off Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: Top Courses Performance */}
        <div className="lg:col-span-2 bg-card border border-border/70 rounded-2xl p-4 sm:p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base text-foreground">Kurslar faolligi va reytingi</h3>
              <p className="text-xs text-muted-foreground mt-0.5">Talabalar soni va muvaffaqiyatli yakunlash foizi</p>
            </div>
            <Link href="/admin/courses" className="text-xs text-primary font-semibold hover:underline">
              Barchasini boshqarish
            </Link>
          </div>

          <div className="space-y-4">
            {courses.map((c) => (
              <div key={c.id} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-foreground">{c.title}</span>
                  <span className="text-muted-foreground">{c.studentsCount} ta talaba ({c.rating} ★)</span>
                </div>
                <div className="w-full h-2.5 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${Math.min(100, Math.round((c.studentsCount / 700) * 100))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Drop-off and Warnings */}
        <div className="bg-card border border-border/70 rounded-2xl p-6 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-amber-500">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <h3 className="font-bold text-sm text-foreground">Tashlab ketish (Drop-off) Tahlili</h3>
            </div>
            <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
              Talabalarning eng ko&apos;p to&apos;xtab qolgan darslari:
            </p>

            <div className="space-y-3 mt-4">
              {(overview?.dropoff || []).length === 0 && (
                <p className="text-xs text-muted-foreground">Tugallanmagan kurs hozircha ajralmadi.</p>
              )}
              {(overview?.dropoff || []).map((item) => (
                <div key={item.title} className="p-3 rounded-xl bg-secondary/50 border border-border/50 text-xs">
                  <p className="font-bold text-foreground">{item.title}</p>
                  <p className="text-[11px] text-amber-400 mt-0.5">{item.note}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 text-xs">
            <span className="font-bold text-primary block">Tavsiya:</span>
            <span className="text-muted-foreground mt-0.5 block">
              Murakkab modullar uchun AI Tyutorni faollashtiring yoki qo&apos;shimcha video materiallar biriktiring.
            </span>
          </div>
        </div>
      </div>

      {/* Recent Registrations Table */}
      <div className="bg-card border border-border/70 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-base text-foreground">So&apos;nggi ro&apos;yxatdan o&apos;tgan foydalanuvchilar</h3>
          <Link href="/admin/users" className="text-xs text-primary font-semibold hover:underline">
            Foydalanuvchilar bo&apos;limi
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-secondary/60 text-muted-foreground border-y border-border/60">
              <tr>
                <th className="py-3 px-4 font-semibold">F.I.O</th>
                <th className="py-3 px-4 font-semibold">Roli</th>
                <th className="py-3 px-4 font-semibold">Tashkilot / Bo&apos;lim</th>
                <th className="py-3 px-4 font-semibold">Vaqt</th>
                <th className="py-3 px-4 font-semibold text-right">Amal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {recentRegistrations.map((u) => (
                <tr key={u.id} className="hover:bg-secondary/30 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-foreground">{u.name}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-semibold text-[10px]">
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-muted-foreground">{u.org}</td>
                  <td className="py-3.5 px-4 text-muted-foreground">{u.date}</td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      href="/admin/users"
                      className="text-primary font-semibold hover:underline"
                    >
                      Boshqarish
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
