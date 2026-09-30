"use client";

import { useState } from "react";
import Link from "next/link";
import { Award, Shield, Phone, Building, Flame, Download, QrCode, ExternalLink, Moon, Sun, CheckCircle } from "lucide-react";
import { Certificate } from "@/types";
import { triggerHaptic } from "@/lib/telegram";
import { useSession } from "@/lib/session";

export default function UserProfilePage() {
  const { user: currentUserMock, certificates: certificatesMock, logout } = useSession();
  const [selectedCert, setSelectedCert] = useState<Certificate | null>(null);
  const [isDark, setIsDark] = useState<boolean>(true);

  const toggleTheme = () => {
    triggerHaptic("light");
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <div className="space-y-4">
      {/* Profile Header Card */}
      <div className="bg-card border border-border/70 rounded-3xl p-5 shadow-sm space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-primary to-indigo-400 p-[2px] shadow-md">
              <div className="w-full h-full rounded-full bg-background flex items-center justify-center font-black text-xl text-primary overflow-hidden">
                {currentUserMock.avatarUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={currentUserMock.avatarUrl} alt="" className="w-full h-full object-cover" />
                ) : (
                  currentUserMock.fullName.charAt(0)
                )}
              </div>
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center space-x-1.5">
                <h2 className="font-bold text-base text-foreground tracking-tight">
                  {currentUserMock.fullName}
                </h2>
                <Shield className="w-4 h-4 text-primary shrink-0" />
              </div>
              <p className="text-xs text-muted-foreground font-medium">
                {[currentUserMock.rank, currentUserMock.position].filter(Boolean).join(", ") || "Tinglovchi"}
              </p>
              <span className="inline-block text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full mt-1">
                {currentUserMock.role === "citizen" ? "Fuqaro" : currentUserMock.role === "officer" ? "Xodim" : currentUserMock.role}
              </span>
            </div>
          </div>

          <div className="flex items-center">
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              logout();
            }}
            className="text-[11px] font-semibold text-muted-foreground underline mr-2"
          >
            Chiqish
          </button>
          <button
            onClick={toggleTheme}
            className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          </div>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/50 text-xs">
          <div className="flex items-center space-x-2 text-muted-foreground p-2 rounded-xl bg-secondary/40">
            <Building className="w-3.5 h-3.5 text-primary shrink-0" />
            <span className="line-clamp-1">{currentUserMock.organization}</span>
          </div>
          <div className="flex items-center space-x-2 text-muted-foreground p-2 rounded-xl bg-secondary/40">
            <Phone className="w-3.5 h-3.5 text-primary shrink-0" />
            <span>{currentUserMock.phone}</span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-2">
        <div className="bg-card border border-border/70 rounded-2xl p-2.5 text-center shadow-sm">
          <span className="text-[10px] text-muted-foreground font-medium block">Ball</span>
          <span className="text-base font-black text-primary">{currentUserMock.points}</span>
        </div>
        <div className="bg-card border border-border/70 rounded-2xl p-2.5 text-center shadow-sm">
          <span className="text-[10px] text-muted-foreground font-medium block">Streak</span>
          <span className="text-base font-black text-amber-500 flex items-center justify-center space-x-0.5">
            <Flame className="w-3.5 h-3.5 fill-amber-500" />
            <span>{currentUserMock.streakDays}</span>
          </span>
        </div>
        <div className="bg-card border border-border/70 rounded-2xl p-2.5 text-center shadow-sm">
          <span className="text-[10px] text-muted-foreground font-medium block">Kurslar</span>
          <span className="text-base font-black text-foreground">{currentUserMock.completedCoursesCount}</span>
        </div>
        <div className="bg-card border border-border/70 rounded-2xl p-2.5 text-center shadow-sm">
          <span className="text-[10px] text-muted-foreground font-medium block">Sertifikat</span>
          <span className="text-base font-black text-emerald-500">{currentUserMock.certificatesCount}</span>
        </div>
      </div>

      {/* Certificates Section */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-sm text-foreground">Sertifikatlarim</h3>
          <span className="text-xs text-muted-foreground">{certificatesMock.length} ta mavjud</span>
        </div>

        <div className="space-y-2.5">
          {certificatesMock.map((cert) => (
            <div
              key={cert.id}
              className="bg-card border border-border/70 rounded-2xl p-3.5 shadow-sm flex items-center justify-between hover:border-primary/50 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center shrink-0">
                  <Award className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-foreground line-clamp-1">
                    {cert.courseTitle}
                  </h4>
                  <p className="text-[10px] text-muted-foreground">
                    № {cert.certificateNumber} • {cert.issueDate}
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  triggerHaptic("medium");
                  setSelectedCert(cert);
                }}
                className="px-3 py-1.5 rounded-xl bg-secondary hover:bg-primary hover:text-primary-foreground text-xs font-semibold text-foreground transition-all shrink-0 flex items-center space-x-1"
              >
                <span>Ko&apos;rish</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {currentUserMock.role === "superadmin" && (
      <div className="pt-2">
        <Link
          href="/admin"
          onClick={() => triggerHaptic("medium")}
          className="w-full py-3 rounded-2xl bg-gradient-to-r from-blue-700 to-indigo-800 text-white text-xs font-bold shadow-md flex items-center justify-center space-x-2 hover:opacity-95 transition-opacity"
        >
          <Shield className="w-4 h-4" />
          <span>Boshqaruv Admin Paneliga O&apos;tish (Desktop)</span>
        </Link>
      </div>
      )}

      {/* Certificate Modal */}
      {selectedCert && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/80 rounded-3xl p-6 max-w-sm w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            {/* Certificate Header Banner */}
            <div className="border-4 border-amber-500/40 rounded-2xl p-4 bg-gradient-to-b from-card to-secondary/30 text-center space-y-3 relative overflow-hidden">
              <div className="space-y-0.5">
                <span className="text-[9px] uppercase tracking-widest text-primary font-bold">
                  O&apos;zbekiston Respublikasi IIV Akademiyasi
                </span>
                <h3 className="font-extrabold text-sm text-foreground uppercase tracking-wide">
                  Rasmiy Sertifikat
                </h3>
              </div>

              <div className="py-2 border-y border-border/60">
                <p className="text-[10px] text-muted-foreground">Muvaffaqiyatli tamomladi:</p>
                <p className="font-black text-sm text-foreground">{selectedCert.studentName}</p>
                <p className="text-[11px] font-semibold text-primary mt-1 line-clamp-1">
                  &ldquo;{selectedCert.courseTitle}&rdquo;
                </p>
              </div>

              <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                <span>№ {selectedCert.certificateNumber}</span>
                <span className="font-bold text-emerald-500">Natija: {selectedCert.scorePercentage}%</span>
              </div>

              {/* QR Code */}
              <div className="pt-1 flex flex-col items-center justify-center">
                <div className="p-1.5 bg-white rounded-lg shadow-sm">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(selectedCert.qrCodeUrl || selectedCert.certificateNumber)}`}
                    alt="QR"
                    className="w-20 h-20"
                  />
                </div>
                <span className="text-[9px] text-muted-foreground mt-1">
                  Haqiqiylikni tasdiqlovchi QR kod
                </span>
              </div>
            </div>

            <div className="flex space-x-2 pt-1">
              <button
                onClick={() => {
                  triggerHaptic("success");
                  alert("PDF sertifikat yuklab olinmoqda...");
                }}
                className="flex-1 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-xs flex items-center justify-center space-x-1.5 shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                <span>PDF Yuklash</span>
              </button>
              <button
                onClick={() => setSelectedCert(null)}
                className="px-4 py-2.5 rounded-xl border border-border/80 text-foreground text-xs font-semibold hover:bg-secondary transition-colors"
              >
                Yopish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
