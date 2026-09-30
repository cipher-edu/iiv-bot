"use client";

import { useState } from "react";
import { Trophy, Flame, Award, Shield, Medal } from "lucide-react";
import { useSession } from "@/lib/session";
import { triggerHaptic } from "@/lib/telegram";

export default function RatingLeaderboardPage() {
  const { user: me, leaderboard, badges } = useSession();
  const [activeTab, setActiveTab] = useState<"leaderboard" | "badges">("leaderboard");

  const topThree = leaderboard.slice(0, 3);
  const others = leaderboard.slice(3);
  const myPlace = leaderboard.find((row) => row.id === me.id);

  return (
    <div className="space-y-4">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">Reyting va Yutuqlar</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Akademiya va sohaviy xodimlar orasida peshqadamlar
        </p>
      </div>

      {/* Tabs */}
      <div className="flex rounded-2xl bg-secondary/70 p-1 border border-border/50">
        <button
          onClick={() => {
            triggerHaptic("light");
            setActiveTab("leaderboard");
          }}
          className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "leaderboard"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Umumiy reyting
        </button>
        <button
          onClick={() => {
            triggerHaptic("light");
            setActiveTab("badges");
          }}
          className={`flex-1 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "badges"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Nishonlar (Badges)
        </button>
      </div>

      {activeTab === "leaderboard" ? (
        <div className="space-y-4">
          {/* Top 3 Podium */}
          <div className="grid grid-cols-3 gap-2 pt-6 items-end">
            {/* 2nd Place */}
            {topThree[1] && (
              <div className="flex flex-col items-center space-y-1.5 text-center">
                <div className="relative">
                  <div className="w-14 h-14 rounded-full border-2 border-slate-300 overflow-hidden bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={topThree[1].avatarUrl} alt="" className="w-full h-full object-cover" />
                  </div>
                  <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-slate-300 text-slate-800 font-black text-[11px] flex items-center justify-center shadow">
                    2
                  </span>
                </div>
                <div className="pt-2">
                  <p className="text-xs font-bold text-foreground line-clamp-1">{topThree[1].fullName}</p>
                  <p className="text-[11px] font-semibold text-primary">{topThree[1].points} b</p>
                </div>
                <div className="w-full h-16 bg-slate-400/10 border-t-2 border-slate-300 rounded-t-xl" />
              </div>
            )}

            {/* 1st Place */}
            {topThree[0] && (
              <div className="flex flex-col items-center space-y-1.5 text-center -mt-6">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full border-2 border-amber-400 overflow-hidden bg-muted shadow-lg shadow-amber-500/20">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={topThree[0].avatarUrl} alt="" className="w-full h-full object-cover" />
                  </div>
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-amber-400">
                    👑
                  </span>
                  <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-amber-400 text-amber-950 font-black text-xs flex items-center justify-center shadow-md">
                    1
                  </span>
                </div>
                <div className="pt-2">
                  <p className="text-xs font-bold text-foreground line-clamp-1">{topThree[0].fullName}</p>
                  <p className="text-xs font-bold text-amber-400">{topThree[0].points} b</p>
                </div>
                <div className="w-full h-24 bg-amber-400/10 border-t-2 border-amber-400 rounded-t-xl" />
              </div>
            )}

            {/* 3rd Place */}
            {topThree[2] && (
              <div className="flex flex-col items-center space-y-1.5 text-center">
                <div className="relative">
                  <div className="w-14 h-14 rounded-full border-2 border-amber-700/60 overflow-hidden bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={topThree[2].avatarUrl} alt="" className="w-full h-full object-cover" />
                  </div>
                  <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-amber-700 text-white font-black text-[11px] flex items-center justify-center shadow">
                    3
                  </span>
                </div>
                <div className="pt-2">
                  <p className="text-xs font-bold text-foreground line-clamp-1">{topThree[2].fullName}</p>
                  <p className="text-[11px] font-semibold text-primary">{topThree[2].points} b</p>
                </div>
                <div className="w-full h-12 bg-amber-700/10 border-t-2 border-amber-700/60 rounded-t-xl" />
              </div>
            )}
          </div>

          {/* Current User Rank Strip */}
          <div className="p-3.5 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="w-7 h-7 rounded-xl bg-primary text-primary-foreground font-black text-xs flex items-center justify-center shadow-sm">
                {myPlace?.rank || "—"}
              </span>
              <div>
                <p className="text-xs font-bold text-foreground">Sizning o&apos;rningiz</p>
                <p className="text-[10px] text-muted-foreground">{me.organization || "IIV Akademiyasi"}</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs font-black text-primary">{me.points} ball</span>
              <p className="text-[10px] text-amber-500 font-semibold flex items-center justify-end space-x-0.5">
                <Flame className="w-3 h-3 fill-amber-500" />
                <span>{me.streakDays} kun</span>
              </p>
            </div>
          </div>

          {/* Full List */}
          <div className="space-y-2">
            {others.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-3 rounded-2xl bg-card border border-border/60 shadow-sm"
              >
                <div className="flex items-center space-x-3">
                  <span className="w-6 text-center text-xs font-bold text-muted-foreground">
                    #{user.rank}
                  </span>
                  <div className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center font-bold text-xs text-primary shrink-0 overflow-hidden">
                    {user.avatarUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={user.avatarUrl} alt="" className="w-full h-full object-cover" />
                    ) : (
                      user.fullName.charAt(0)
                    )}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-foreground">{user.fullName}</h4>
                    <p className="text-[10px] text-muted-foreground line-clamp-1">{user.organization}</p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-xs font-bold text-foreground">{user.points} b</span>
                  <span className="text-[10px] text-muted-foreground block">{user.streakDays} kun streak</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Badges Tab */
        <div className="grid grid-cols-2 gap-3">
          {badges.length === 0 && (
            <p className="col-span-2 text-sm text-muted-foreground">Hozircha nishonlar ro&apos;yxati bo&apos;sh.</p>
          )}
          {badges.map((badge) => (
            <div
              key={badge.id}
              className={`p-4 rounded-2xl border text-center space-y-2 transition-all ${
                badge.isUnlocked
                  ? "bg-card border-border/80 shadow-sm"
                  : "bg-secondary/40 border-dashed border-border/50 opacity-60"
              }`}
            >
              <div className="w-12 h-12 rounded-2xl bg-secondary flex items-center justify-center text-2xl mx-auto shadow-inner">
                {badge.icon}
              </div>
              <div>
                <h4 className="font-bold text-xs text-foreground">{badge.name}</h4>
                <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">
                  {badge.description}
                </p>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full inline-block ${
                  badge.isUnlocked
                    ? "bg-emerald-500/10 text-emerald-500"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {badge.isUnlocked ? "Ochilgan" : "Qulflangan"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
