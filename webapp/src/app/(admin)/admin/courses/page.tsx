"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search, Edit2, Trash2, Eye, Star, BookOpen, Users } from "lucide-react";
import { Course } from "@/types";
import { api } from "@/lib/api";

export default function AdminCoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api<Course[]>("/api/v1/admin/courses").then(setCourses).catch(() => setCourses([]));
  }, []);

  const filtered = courses.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.instructor.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            O&apos;quv Kurslari Konstruktori
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Kurslar, o&apos;quv modullari va dars materiallarini boshqarish
          </p>
        </div>

        <Link
          href="/admin/courses/new"
          className="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold shadow-md transition-all flex items-center space-x-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>Yangi kurs yaratish</span>
        </Link>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between bg-card border border-border/70 p-4 rounded-2xl shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Kurs yoki o'qituvchi nomi..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all"
          />
        </div>

        <div className="flex items-center space-x-2 text-xs text-muted-foreground">
          <span>Jami: <strong className="text-foreground">{courses.length}</strong> ta kurs</span>
        </div>
      </div>

      {/* Courses Table */}
      <div className="bg-card border border-border/70 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-secondary/60 text-muted-foreground border-b border-border/60">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Kurs Nomi</th>
                <th className="py-3.5 px-4 font-semibold">Toifasi</th>
                <th className="py-3.5 px-4 font-semibold">O&apos;qituvchi</th>
                <th className="py-3.5 px-4 font-semibold">Darslar soni</th>
                <th className="py-3.5 px-4 font-semibold">Talabalar</th>
                <th className="py-3.5 px-4 font-semibold">Holat</th>
                <th className="py-3.5 px-4 font-semibold text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {filtered.map((course) => (
                <tr key={course.id} className="hover:bg-secondary/20 transition-colors">
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-3">
                      {course.coverImage ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img
                          src={course.coverImage}
                          alt=""
                          className="w-10 h-10 rounded-xl object-cover shrink-0 bg-secondary"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-xl bg-secondary shrink-0" />
                      )}
                      <div>
                        <h4 className="font-bold text-foreground text-xs">{course.title}</h4>
                        <div className="flex items-center space-x-1 text-amber-500 font-semibold text-[11px] mt-0.5">
                          <Star className="w-3 h-3 fill-amber-500" />
                          <span>{course.rating}</span>
                          <span className="text-muted-foreground">({course.reviewsCount} baho)</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-muted-foreground font-medium">
                    {course.category}
                  </td>
                  <td className="py-4 px-4 font-semibold text-foreground">
                    {course.instructor}
                  </td>
                  <td className="py-4 px-4 text-muted-foreground font-semibold">
                    {course.lessonsCount} ta
                  </td>
                  <td className="py-4 px-4 font-bold text-foreground">
                    {course.studentsCount} nafar
                  </td>
                  <td className="py-4 px-4">
                    <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] uppercase tracking-wider bg-emerald-500/10 text-emerald-500">
                      {course.status === "published" ? "Faol" : "Qoralama"}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end space-x-1.5">
                      <Link
                        href={`/courses/${course.id}`}
                        target="_blank"
                        title="Ko'rish"
                        className="p-1.5 rounded-lg bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        title="Tahrirlash"
                        className="p-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-500 transition-colors"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        title="O'chirish"
                        onClick={() => {
                          if (!confirm("Ushbu kursni o'chirishni tasdiqlaysizmi?")) return;
                          api(`/api/v1/admin/courses/${course.id}`, { method: "DELETE" })
                            .then(() => setCourses((prev) => prev.filter((item) => item.id !== course.id)))
                            .catch((err: Error) => alert(err.message));
                        }}
                        className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
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
