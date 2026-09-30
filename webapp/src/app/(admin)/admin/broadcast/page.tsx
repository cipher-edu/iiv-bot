"use client";

import { useEffect, useState } from "react";
import { Megaphone, Send, Users, ShieldCheck, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function AdminBroadcastPage() {
  const [segment, setSegment] = useState("all");
  const [message, setMessage] = useState(
    "Hurmatli tinglovchilar! Kiberxavfsizlik oyligi doirasida yangi dars moduli platformaga joylandi. Bugunoq o'z bilimingizni sinab ko'ring va qo'shimcha ballarga ega bo'ling!"
  );
  const [buttonText, setButtonText] = useState("Darsni boshlash");
  const [buttonUrl, setButtonUrl] = useState("https://t.me/nsusupportbot/app");
  const [isSending, setIsSending] = useState(false);
  const [sentSuccess, setSentSuccess] = useState(false);

  const [audienceCounts, setAudienceCounts] = useState<Record<string, number>>({
    all: 0,
    officers: 0,
    citizens: 0,
    active_streak: 0,
  });
  const [sentNote, setSentNote] = useState("");

  useEffect(() => {
    api<Record<string, number>>("/api/v1/admin/audiences")
      .then(setAudienceCounts)
      .catch(() => undefined);
  }, []);

  const handleSendBroadcast = async () => {
    if (!message.trim()) return;
    setIsSending(true);
    setSentSuccess(false);
    try {
      const result = await api<{ sent: number; failed: number; targeted: number }>(
        "/api/v1/admin/broadcast",
        {
          method: "POST",
          body: JSON.stringify({ segment, message, buttonText, buttonUrl }),
        }
      );
      setSentNote(`${result.sent} ta yuborildi, ${result.failed} ta xato, jami ${result.targeted}`);
      setSentSuccess(true);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Yuborilmadi");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black tracking-tight text-foreground">
          Ommaviy Xabarnoma (Broadcast) Yuborish
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Telegram bot orqali foydalanuvchilar segmentlariga tezkor xabarlar tarqatish
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Left Form: 3 cols */}
        <div className="lg:col-span-3 bg-card border border-border/70 rounded-2xl p-4 sm:p-6 shadow-sm space-y-4">
          <h3 className="font-bold text-sm text-foreground flex items-center space-x-2">
            <Megaphone className="w-4 h-4 text-primary" />
            <span>Xabarnoma parametrlari</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="font-semibold text-foreground">Qabul qiluvchilar auditoriyasi (Segment)</label>
              <select
                value={segment}
                onChange={(e) => setSegment(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground focus:ring-1 focus:ring-primary"
              >
                <option value="all">Barchaga yuborish ({audienceCounts.all} nafar)</option>
                <option value="officers">Faqat IIV xodimlari ({audienceCounts.officers} nafar)</option>
                <option value="citizens">Faqat fuqarolar ({audienceCounts.citizens} nafar)</option>
                <option value="active_streak">Faol o&apos;quvchilar, streak 5+ ({audienceCounts.active_streak} nafar)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Xabar matni</label>
              <textarea
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full p-3 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground leading-relaxed focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">Inline tugma matni (Ixtiyoriy)</label>
                <input
                  type="text"
                  value={buttonText}
                  onChange={(e) => setButtonText(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">Tugma havolasi (URL)</label>
                <input
                  type="text"
                  value={buttonUrl}
                  onChange={(e) => setButtonUrl(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground"
                />
              </div>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between border-t border-border/50">
            <span className="text-xs text-muted-foreground">
              Qamrov: <strong className="text-primary font-bold">{audienceCounts[segment] || 0}</strong> nafar Telegram foydalanuvchi
            </span>

            <button
              onClick={handleSendBroadcast}
              disabled={isSending || !message.trim()}
              className="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-xs shadow-md transition-transform active:scale-95 disabled:opacity-50 flex items-center space-x-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isSending ? "Xabar tarqatilmoqda..." : "Yuborishni boshlash"}</span>
            </button>
          </div>

          {sentSuccess && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 flex items-center space-x-2 text-xs font-semibold animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{sentNote || "Xabarlar yuborildi"}</span>
            </div>
          )}
        </div>

        {/* Right: Live Telegram Preview (2 cols) */}
        <div className="lg:col-span-2 space-y-2">
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">
            Telegramdagi Jonli Ko&apos;rinish
          </span>

          <div className="bg-[#182533] text-white rounded-3xl p-4 shadow-xl border border-white/10 space-y-3">
            <div className="flex items-center space-x-2 pb-2 border-b border-white/10">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center font-bold text-xs">
                IIV
              </div>
              <div>
                <p className="text-xs font-bold leading-tight">IIV EduBot</p>
                <p className="text-[10px] text-blue-300">bot</p>
              </div>
            </div>

            {/* Bubble */}
            <div className="bg-[#2b5278] rounded-2xl rounded-tl-sm p-3.5 text-xs leading-relaxed space-y-2.5">
              <p className="whitespace-pre-line text-slate-100">{message || "Xabar matni..."}</p>
              <span className="text-[9px] text-slate-300 block text-right">09:40</span>
            </div>

            {/* Inline Button */}
            {buttonText && (
              <div className="pt-1">
                <button className="w-full py-2.5 rounded-xl bg-[#2b5278] hover:bg-[#34628f] text-center text-xs font-semibold text-white shadow transition-colors">
                  {buttonText}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
