"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Database, HardDrive, Cpu, Activity, AlertOctagon, CheckCircle2, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

interface AuditPayload {
  services: { name: string; status: string; latency: string; port: number | string }[];
  events: { id: number; action: string; actor: string; details: string; ip: string; status: string; time: string }[];
}

export default function AdminAuditPage() {
  const [systemServices, setSystemServices] = useState<AuditPayload["services"]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditPayload["events"]>([]);

  const reload = () => {
    api<AuditPayload>("/api/v1/admin/audit")
      .then((payload) => {
        setSystemServices(payload.services);
        setAuditEvents(payload.events);
      })
      .catch(() => undefined);
  };

  useEffect(() => {
    reload();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            Xavfsizlik & Tizim Audit Jurnali
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Server xizmatlari holati, kiberxavfsizlik hodisalari va barcha ma&apos;muriy harakatlar qaydi
          </p>
        </div>

        <button
          onClick={reload}
          className="px-3.5 py-2 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground text-xs font-semibold flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Qayta tekshirish</span>
        </button>
      </div>

      {/* Services Health Status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {systemServices.map((srv, idx) => (
          <div key={idx} className="bg-card border border-border/70 rounded-2xl p-4 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-foreground line-clamp-1">{srv.name}</span>
              <div className={`w-2.5 h-2.5 rounded-full border-2 animate-pulse ${srv.status === "Operational" ? "bg-emerald-500 border-emerald-500" : "bg-red-500 border-red-500"}`} />
            </div>
            <div className="flex items-center justify-between text-xs pt-1">
              <span className={`font-bold ${srv.status === "Operational" ? "text-emerald-500" : "text-red-400"}`}>{srv.status}</span>
              <span className="text-muted-foreground">{srv.latency}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Audit Log Table */}
      <div className="bg-card border border-border/70 rounded-2xl shadow-sm overflow-hidden space-y-3 p-5">
        <h3 className="font-bold text-sm text-foreground">So&apos;nggi hodisalar va harakatlar tarixi</h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-secondary/60 text-muted-foreground border-y border-border/60">
              <tr>
                <th className="py-3 px-3.5 font-semibold">Harakat / Hodisa</th>
                <th className="py-3 px-3.5 font-semibold">Bajaruvchi</th>
                <th className="py-3 px-3.5 font-semibold">Tafsilotlar</th>
                <th className="py-3 px-3.5 font-semibold">IP Manzil</th>
                <th className="py-3 px-3.5 font-semibold">Holat</th>
                <th className="py-3 px-3.5 font-semibold text-right">Vaqt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {auditEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-secondary/20 transition-colors">
                  <td className="py-3.5 px-3.5 font-bold text-foreground">{evt.action}</td>
                  <td className="py-3.5 px-3.5 font-semibold text-primary">{evt.actor}</td>
                  <td className="py-3.5 px-3.5 text-muted-foreground">{evt.details}</td>
                  <td className="py-3.5 px-3.5 font-mono text-[11px] text-muted-foreground">{evt.ip}</td>
                  <td className="py-3.5 px-3.5">
                    <span
                      className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                        evt.status === "Success"
                          ? "bg-emerald-500/10 text-emerald-500"
                          : evt.status === "Warning"
                          ? "bg-amber-500/10 text-amber-500"
                          : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      {evt.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-3.5 text-muted-foreground text-right">{evt.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
