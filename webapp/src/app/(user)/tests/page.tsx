"use client";

import Link from "next/link";
import { CheckSquare, Clock, Trophy, AlertCircle, ChevronRight } from "lucide-react";
import { useSession } from "@/lib/session";
import { triggerHaptic } from "@/lib/telegram";

export default function TestsCatalogPage() {
  const { tests } = useSession();
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">Bilimni sinash (Testlar)</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Attestatsiya va kurslar bo&apos;yicha oraliq/yakuniy testlar
        </p>
      </div>

      <div className="space-y-3">
        {tests.length === 0 && (
          <p className="text-sm text-muted-foreground">Hozircha faol test yo&apos;q.</p>
        )}
        {tests.map((test) => (
          <div
            key={test.id}
            className="bg-card border border-border/70 rounded-2xl p-4 shadow-sm space-y-3 hover:border-primary/50 transition-colors"
          >
            <div className="flex items-start justify-between space-x-2">
              <div className="space-y-1 flex-1">
                {(test.courseTitle || test.moduleTitle || test.lessonTitle) && (
                  <span className="text-[11px] font-semibold text-primary uppercase tracking-wide">
                    {[test.courseTitle, test.moduleTitle, test.lessonTitle].filter(Boolean).join(" · ")}
                  </span>
                )}
                <h3 className="font-bold text-sm text-foreground tracking-tight">
                  {test.title}
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {test.description}
                </p>
              </div>

              {test.userBestScore !== undefined && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-xl px-2.5 py-1 text-center shrink-0">
                  <span className="text-[10px] uppercase font-bold block">Natija</span>
                  <span className="text-sm font-extrabold">{test.userBestScore}%</span>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/40">
              <div className="flex items-center space-x-3">
                <span className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{test.durationMinutes} daqiqa</span>
                </span>
                <span className="flex items-center space-x-1">
                  <CheckSquare className="w-3.5 h-3.5" />
                  <span>{test.questionsCount} savol</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Trophy className="w-3.5 h-3.5" />
                  <span>O&apos;tish: {test.passPercentage}%</span>
                </span>
              </div>

              <Link
                href={`/tests/${test.id}`}
                onClick={() => triggerHaptic("medium")}
                className="px-3.5 py-1.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold shadow-sm transition-transform active:scale-95 flex items-center space-x-1"
              >
                <span>Boshlash</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
