"use client";

import Link from "next/link";
import { BookOpen, CheckSquare, Award, Play, ChevronRight, Flame, Sparkles } from "lucide-react";
import { useSession } from "@/lib/session";

export default function UserHomePage() {
  const { user, courses, tests } = useSession();
  const activeCourse =
    courses.find((course) => (course.progressPercentage || 0) < 100) || courses[0];
  const quickTest = tests[0];

  return (
    <div className="space-y-5">
      {/* Hero Streak Card */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-5 text-white shadow-lg">
        <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-white/10 rounded-full blur-xl pointer-events-none" />
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded-full backdrop-blur-md">
                Kunlik maqsad
              </span>
            </div>
            <h2 className="text-xl font-bold mt-2 tracking-tight">
              {user.streakDays}-kunlik seriya davom etmoqda!
            </h2>
            <p className="text-xs text-blue-100/90 mt-1 max-w-[240px]">
              Bugungi 1 ta darsni yakunlang va +15 ball bonusni qo&apos;lga kiriting.
            </p>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/30 shadow-inner">
            <Flame className="w-7 h-7 text-amber-300 fill-amber-300 animate-pulse" />
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-white/15 flex items-center justify-between text-xs">
          <span>{user.points} ball</span>
          <Link
            href="/rating"
            className="flex items-center space-x-1 font-semibold underline decoration-white/50 hover:decoration-white"
          >
            <span>Reytingni ko&apos;rish</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-3 gap-3">
        <Link
          href="/courses"
          className="bg-card hover:bg-card/80 border border-border/60 rounded-xl p-3 flex flex-col items-center justify-center text-center space-y-1.5 transition-all shadow-sm active:scale-95"
        >
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center">
            <BookOpen className="w-5 h-5" />
          </div>
          <span className="text-xs font-medium text-foreground">Kurslar</span>
        </Link>

        <Link
          href="/tests"
          className="bg-card hover:bg-card/80 border border-border/60 rounded-xl p-3 flex flex-col items-center justify-center text-center space-y-1.5 transition-all shadow-sm active:scale-95"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
            <CheckSquare className="w-5 h-5" />
          </div>
          <span className="text-xs font-medium text-foreground">Testlar</span>
        </Link>

        <Link
          href="/profile"
          className="bg-card hover:bg-card/80 border border-border/60 rounded-xl p-3 flex flex-col items-center justify-center text-center space-y-1.5 transition-all shadow-sm active:scale-95"
        >
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center">
            <Award className="w-5 h-5" />
          </div>
          <span className="text-xs font-medium text-foreground">Sertifikat</span>
        </Link>
      </div>

      {/* Continue Learning Section */}
      {activeCourse && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base tracking-tight text-foreground">Davom ettirish</h3>
            <Link href="/courses" className="text-xs text-primary font-medium hover:underline">
              Barchasi
            </Link>
          </div>

          <div className="bg-card border border-border/60 rounded-2xl p-4 shadow-sm space-y-3">
            <div className="flex items-start justify-between space-x-3">
              <div className="space-y-1 flex-1">
                <span className="text-[11px] font-semibold text-primary uppercase tracking-wider">
                  {activeCourse.category}
                </span>
                <h4 className="font-semibold text-sm text-foreground line-clamp-1">
                  {activeCourse.title}
                </h4>
                <p className="text-xs text-muted-foreground line-clamp-1">
                  {activeCourse.lessonsCount} ta dars • {activeCourse.instructor}
                </p>
              </div>
              <Link
                href={`/courses/${activeCourse.id}`}
                className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0 shadow-md hover:bg-primary/90 transition-transform active:scale-90"
              >
                <Play className="w-4 h-4 fill-current ml-0.5" />
              </Link>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-[11px] text-muted-foreground font-medium">
                <span>O&apos;zlashtirish</span>
                <span>{activeCourse.progressPercentage}%</span>
              </div>
              <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${activeCourse.progressPercentage}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Test Recommendation */}
      {quickTest && (
      <div className="bg-gradient-to-r from-emerald-950/40 via-card to-card border border-emerald-500/30 rounded-2xl p-4 shadow-sm flex items-center justify-between space-x-3">
        <div className="space-y-1">
          <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Navbatdagi test</span>
          </div>
          <h4 className="font-bold text-sm text-foreground">{quickTest.title}</h4>
          <p className="text-[11px] text-muted-foreground">
            {quickTest.questionsCount} ta savol • {quickTest.durationMinutes} daqiqa
          </p>
        </div>
        <Link
          href={`/tests/${quickTest.id}`}
          className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm shrink-0 transition-transform active:scale-95"
        >
          Boshlash
        </Link>
      </div>
      )}

      {/* AI Assistant Banner */}
      <div className="bg-card border border-border/60 rounded-2xl p-4 shadow-sm flex items-center space-x-3">
        <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-400 flex items-center justify-center shrink-0">
          <Sparkles className="w-6 h-6" />
        </div>
        <div className="flex-1 space-y-0.5">
          <h4 className="font-semibold text-sm text-foreground">AI Tyutordan so&apos;rang</h4>
          <p className="text-xs text-muted-foreground">
            Darslar yoki qonunchilik bo&apos;yicha savollaringiz bormi?
          </p>
        </div>
        <Link
          href="/ai-tutor"
          className="text-xs font-semibold text-purple-400 hover:text-purple-300 underline shrink-0"
        >
          Savol berish
        </Link>
      </div>
    </div>
  );
}
