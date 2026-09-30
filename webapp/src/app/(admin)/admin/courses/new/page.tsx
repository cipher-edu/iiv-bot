"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, Trash2, Video, FileText, CheckCircle, Save } from "lucide-react";
import { api, getToken } from "@/lib/api";

export default function NewCourseBuilderPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Axborot texnologiyalari");
  const [instructor, setInstructor] = useState("");
  const [durationHours, setDurationHours] = useState(12);
  const [description, setDescription] = useState("");
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [syllabusFiles, setSyllabusFiles] = useState<File[]>([]);

  const [modules, setModules] = useState([
    {
      id: 1,
      title: "1-Modul: Kirish va asosiy tushunchalar",
      lessons: [
        { id: 1, title: "1.1 Kirish darsi", duration: 15, videoUrl: "", content: "Dars matni shu yerda kiritiladi..." }
      ]
    }
  ]);

  const handleAddModule = () => {
    setModules((prev) => [
      ...prev,
      {
        id: Date.now(),
        title: `${prev.length + 1}-Modul: Yangi modul nomi`,
        lessons: [{ id: Date.now() + 1, title: "Yangi dars", duration: 15, videoUrl: "", content: "" }]
      }
    ]);
  };

  const handleAddLesson = (moduleId: number) => {
    setModules((prev) =>
      prev.map((m) => {
        if (m.id === moduleId) {
          return {
            ...m,
            lessons: [
              ...m.lessons,
              { id: Date.now(), title: `Yangi dars ${m.lessons.length + 1}`, duration: 20, videoUrl: "", content: "" }
            ]
          };
        }
        return m;
      })
    );
  };

  const uploadFile = async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const headers = new Headers();
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch("/bot-api/api/v1/admin/uploads", {
      method: "POST",
      headers,
      body: form,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Fayl yuklanmadi");
    }
    return data as { url: string; title: string; type: string };
  };

  const handleSave = async (status: "draft" | "published") => {
    try {
      const cover = coverFile ? await uploadFile(coverFile) : null;
      const files = [];
      for (const file of syllabusFiles) {
        files.push(await uploadFile(file));
      }
      await api("/api/v1/admin/courses", {
        method: "POST",
        body: JSON.stringify({
          title,
          category,
          instructor,
          durationHours,
          description,
          coverUrl: cover?.url || "",
          syllabusFiles: files,
          status,
          modules,
        }),
      });
      router.push("/admin/courses");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Saqlanmadi");
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/admin/courses"
          className="flex items-center space-x-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Kurslar ro&apos;yxatiga qaytish</span>
        </Link>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleSave("draft")}
            className="px-4 py-2 rounded-xl border border-border/80 text-xs font-semibold hover:bg-secondary text-foreground transition-colors"
          >
            Qoralama sifatida saqlash
          </button>
          <button
            onClick={() => handleSave("published")}
            className="px-5 py-2 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold shadow-md transition-transform active:scale-95 flex items-center space-x-1"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Kursni e&apos;lon qilish</span>
          </button>
        </div>
      </div>

      <h1 className="text-2xl font-black tracking-tight text-foreground">
        Yangi Kurs Yaratish Konstruktori
      </h1>

      {/* Main Details */}
      <div className="bg-card border border-border/70 rounded-2xl p-6 shadow-sm space-y-4">
        <h3 className="font-bold text-sm text-foreground">Kurs Asosiy Ma&apos;lumotlari</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="sm:col-span-2 space-y-1.5">
            <label className="font-semibold text-foreground">Kurs nomi</label>
            <input
              type="text"
              placeholder="Masalan: Tezkor-qidiruv faoliyatida axborot tahlili"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
            />
          </div>

          <div className="space-y-1.5">
            <label className="font-semibold text-foreground">Kategoriya / Yo&apos;nalish</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
            >
              <option value="Axborot texnologiyalari">Axborot texnologiyalari</option>
              <option value="Yo'l harakati">Yo&apos;l harakati xavfsizligi</option>
              <option value="Tergov va Kriminalistika">Tergov va Kriminalistika</option>
              <option value="Huquqshunoslik">Huquqshunoslik va profilaktika</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="font-semibold text-foreground">Mas&apos;ul o&apos;qituvchi / Kafedra</label>
            <input
              type="text"
              placeholder="Masalan: Polkovnik A. Saidov"
              value={instructor}
              onChange={(e) => setInstructor(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
            />
          </div>

          <div className="sm:col-span-2 space-y-1.5">
            <label className="font-semibold text-foreground">Kurs tavsifi (Qisqacha mazmuni)</label>
            <textarea
              rows={3}
              placeholder="Kurs kimlar uchun mo'ljallangan va qanday bilimlar beriladi..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
            />
          </div>

          <div className="sm:col-span-2 space-y-1.5">
            <label className="font-semibold text-foreground">Kurs surati</label>
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              onChange={(e) => setCoverFile(e.target.files?.[0] || null)}
              className="w-full text-xs file:mr-3 file:rounded-lg file:border-0 file:bg-primary file:px-3 file:py-2 file:text-xs file:font-semibold file:text-primary-foreground"
            />
            {coverFile && <p className="text-[11px] text-muted-foreground">{coverFile.name}</p>}
          </div>

          <div className="sm:col-span-2 space-y-1.5">
            <label className="font-semibold text-foreground">Silabus fayllari (istalgancha)</label>
            <input
              type="file"
              multiple
              onChange={(e) => setSyllabusFiles(Array.from(e.target.files || []))}
              className="w-full text-xs file:mr-3 file:rounded-lg file:border-0 file:bg-secondary file:px-3 file:py-2 file:text-xs file:font-semibold"
            />
            {syllabusFiles.length > 0 && (
              <ul className="text-[11px] text-muted-foreground space-y-1">
                {syllabusFiles.map((file) => (
                  <li key={file.name}>{file.name}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Modules & Lessons Curriculum */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-base text-foreground">Modullar va Darslar Sillabusi</h3>
          <button
            onClick={handleAddModule}
            className="px-3.5 py-1.5 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground text-xs font-semibold flex items-center space-x-1"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>+ Modul qo&apos;shish</span>
          </button>
        </div>

        {modules.map((mod, mIdx) => (
          <div key={mod.id} className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border/60">
              <input
                type="text"
                value={mod.title}
                onChange={(e) => {
                  const val = e.target.value;
                  setModules((prev) =>
                    prev.map((m) => (m.id === mod.id ? { ...m, title: val } : m))
                  );
                }}
                className="font-bold text-sm text-foreground bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-primary rounded px-1 flex-1 mr-4"
              />

              <button
                onClick={() => setModules((prev) => prev.filter((m) => m.id !== mod.id))}
                className="text-red-400 hover:text-red-500 p-1 rounded"
                title="Modulni o'chirish"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            {/* Lessons List in Module */}
            <div className="space-y-3">
              {mod.lessons.map((lesson, lIdx) => (
                <div key={lesson.id} className="p-3.5 rounded-xl bg-secondary/40 border border-border/50 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-primary">Dars #{lIdx + 1}</span>
                    <button
                      onClick={() =>
                        setModules((prev) =>
                          prev.map((m) =>
                            m.id === mod.id
                              ? { ...m, lessons: m.lessons.filter((l) => l.id !== lesson.id) }
                              : m
                          )
                        )
                      }
                      className="text-muted-foreground hover:text-red-400"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    <input
                      type="text"
                      placeholder="Dars sarlavhasi..."
                      value={lesson.title}
                      onChange={(e) => {
                        const val = e.target.value;
                        setModules((prev) =>
                          prev.map((m) =>
                            m.id === mod.id
                              ? {
                                  ...m,
                                  lessons: m.lessons.map((l) =>
                                    l.id === lesson.id ? { ...l, title: val } : l
                                  ),
                                }
                              : m
                          )
                        );
                      }}
                      className="w-full px-3 py-2 rounded-lg bg-card border border-border/60 text-xs text-foreground"
                    />

                    <input
                      type="text"
                      placeholder="Video havola (YouTube / MinIO S3)..."
                      value={lesson.videoUrl}
                      onChange={(e) => {
                        const val = e.target.value;
                        setModules((prev) =>
                          prev.map((m) =>
                            m.id === mod.id
                              ? {
                                  ...m,
                                  lessons: m.lessons.map((l) =>
                                    l.id === lesson.id ? { ...l, videoUrl: val } : l
                                  ),
                                }
                              : m
                          )
                        );
                      }}
                      className="w-full px-3 py-2 rounded-lg bg-card border border-border/60 text-xs text-foreground"
                    />
                  </div>
                </div>
              ))}

              <button
                onClick={() => handleAddLesson(mod.id)}
                className="w-full py-2 rounded-xl border border-dashed border-border/80 text-xs text-muted-foreground hover:text-foreground hover:border-primary transition-colors flex items-center justify-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Ushbu modulga dars qo&apos;shish</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
