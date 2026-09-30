"use client";

import { useEffect, useState } from "react";
import { Users, Search, Shield, Ban, CheckCircle, ShieldAlert, X } from "lucide-react";
import { UserRole } from "@/types";
import { api } from "@/lib/api";

interface ManagedUser {
  id: number;
  telegramId: number;
  fullName: string;
  phone: string;
  role: UserRole;
  organization: string;
  rank?: string;
  points: number;
  isBanned: boolean;
  banReason?: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<ManagedUser[]>([]);

  useEffect(() => {
    api<ManagedUser[]>("/api/v1/admin/users").then(setUsers).catch(() => setUsers([]));
  }, []);

  const [search, setSearch] = useState("");
  const [banModalUser, setBanModalUser] = useState<ManagedUser | null>(null);
  const [banDuration, setBanDuration] = useState("1 kun");
  const [banReasonInput, setBanReasonInput] = useState("");

  const handleRoleChange = (userId: number, newRole: UserRole) => {
    api(`/api/v1/admin/users/${userId}/role`, {
      method: "POST",
      body: JSON.stringify({ role: newRole }),
    })
      .then(() =>
        setUsers((prev) => prev.map((user) => (user.id === userId ? { ...user, role: newRole } : user)))
      )
      .catch((err: Error) => alert(err.message));
  };

  const handleBanSubmit = () => {
    if (!banModalUser) return;
    const reason = banReasonInput || "Qoidabuzarlik";
    api(`/api/v1/admin/users/${banModalUser.id}/block`, {
      method: "POST",
      body: JSON.stringify({ duration: banDuration, reason }),
    })
      .then(() => {
        setUsers((prev) =>
          prev.map((user) =>
            user.id === banModalUser.id
              ? { ...user, isBanned: true, banReason: `${banDuration}: ${reason}` }
              : user
          )
        );
        setBanModalUser(null);
        setBanReasonInput("");
      })
      .catch((err: Error) => alert(err.message));
  };

  const handleUnban = (userId: number) => {
    api(`/api/v1/admin/users/${userId}/unblock`, { method: "POST" })
      .then(() =>
        setUsers((prev) =>
          prev.map((user) => (user.id === userId ? { ...user, isBanned: false, banReason: undefined } : user))
        )
      )
      .catch((err: Error) => alert(err.message));
  };

  const filtered = users.filter((u) =>
    u.fullName.toLowerCase().includes(search.toLowerCase()) ||
    u.organization.toLowerCase().includes(search.toLowerCase()) ||
    u.phone.includes(search)
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black tracking-tight text-foreground">
          Foydalanuvchilar va Rollarni Boshqarish
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Tizimdagi xodimlar va fuqarolar ro&apos;yxati, rollar tayinlash hamda xavfsizlik nazorati
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between bg-card border border-border/70 p-4 rounded-2xl shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="F.I.O, telefon yoki tashkilot..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all"
          />
        </div>

        <div className="text-xs text-muted-foreground">
          Jami: <strong className="text-foreground">{users.length}</strong> nafar foydalanuvchi
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-card border border-border/70 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-xs">
          <thead className="bg-secondary/60 text-muted-foreground border-b border-border/60">
            <tr>
              <th className="py-3.5 px-4 font-semibold">F.I.O va Telefon</th>
              <th className="py-3.5 px-4 font-semibold">Tashkilot / Bo&apos;lim</th>
              <th className="py-3.5 px-4 font-semibold">Roli</th>
              <th className="py-3.5 px-4 font-semibold">Ball</th>
              <th className="py-3.5 px-4 font-semibold">Holat</th>
              <th className="py-3.5 px-4 font-semibold text-right">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40">
            {filtered.map((user) => (
              <tr key={user.id} className="hover:bg-secondary/20 transition-colors">
                <td className="py-4 px-4">
                  <div className="space-y-0.5">
                    <p className="font-bold text-foreground text-xs">{user.fullName}</p>
                    <p className="text-[11px] text-muted-foreground">{user.phone} • ID: {user.telegramId}</p>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <p className="text-foreground font-medium">{user.organization}</p>
                  {user.rank && <p className="text-[11px] text-primary">{user.rank}</p>}
                </td>
                <td className="py-4 px-4">
                  <select
                    value={user.role}
                    onChange={(e) => handleRoleChange(user.id, e.target.value as UserRole)}
                    className="px-2.5 py-1 rounded-lg bg-secondary/80 border border-border/70 text-xs font-semibold text-foreground focus:ring-1 focus:ring-primary"
                  >
                    <option value="citizen">Fuqaro</option>
                    <option value="officer">Xodim</option>
                    <option value="moderator">Moderator</option>
                    <option value="admin">Administrator</option>
                    <option value="superadmin">Superadmin</option>
                  </select>
                </td>
                <td className="py-4 px-4 font-bold text-foreground">
                  {user.points} b
                </td>
                <td className="py-4 px-4">
                  {user.isBanned ? (
                    <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 font-bold text-[10px]">
                      Bloklangan
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-bold text-[10px]">
                      Faol
                    </span>
                  )}
                </td>
                <td className="py-4 px-4 text-right">
                  {user.isBanned ? (
                    <button
                      onClick={() => handleUnban(user.id)}
                      className="px-3 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 font-bold text-xs"
                    >
                      Blokdan chiqarish
                    </button>
                  ) : (
                    <button
                      onClick={() => setBanModalUser(user)}
                      className="px-3 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 font-bold text-xs flex items-center space-x-1 ml-auto"
                    >
                      <Ban className="w-3 h-3" />
                      <span>Bloklash</span>
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>

      {/* Ban Modal */}
      {banModalUser && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/80 rounded-3xl p-6 max-w-md w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-2 border-b border-border/60">
              <div className="flex items-center space-x-2 text-red-500">
                <ShieldAlert className="w-5 h-5" />
                <h3 className="font-bold text-sm text-foreground">
                  Foydalanuvchini Bloklash: {banModalUser.fullName}
                </h3>
              </div>
              <button onClick={() => setBanModalUser(null)} className="text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">Bloklash muddati</label>
                <select
                  value={banDuration}
                  onChange={(e) => setBanDuration(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground"
                >
                  <option value="1 soat">1 soat</option>
                  <option value="1 kun">1 kun (24 soat)</option>
                  <option value="7 kun">7 kun (1 hafta)</option>
                  <option value="30 kun">30 kun (1 oy)</option>
                  <option value="Muddatsiz">Muddatsiz (Doimiy)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">Bloklash sababi (Foydalanuvchiga yuboriladi)</label>
                <textarea
                  rows={3}
                  placeholder="Sababni batafsil yozing..."
                  value={banReasonInput}
                  onChange={(e) => setBanReasonInput(e.target.value)}
                  className="w-full p-3 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>
            </div>

            <div className="flex space-x-2 pt-2">
              <button
                onClick={handleBanSubmit}
                className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-md transition-colors"
              >
                Bloklashni tasdiqlash
              </button>
              <button
                onClick={() => setBanModalUser(null)}
                className="px-4 py-2.5 rounded-xl border border-border/80 text-foreground text-xs font-semibold hover:bg-secondary"
              >
                Bekor qilish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
