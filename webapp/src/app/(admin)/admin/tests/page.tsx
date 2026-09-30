"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Sparkles, PenLine, Plus, Trash2, CheckCircle2 } from "lucide-react";
import { Course, TestItem } from "@/types";
import { api } from "@/lib/api";

type Mode = "ai" | "manual";
type Scope = "module" | "lesson";

interface OptionDraft {
  text: string;
  isCorrect: boolean;
}

interface QuestionDraft {
  id: string;
  text: string;
  options: OptionDraft[];
}

const blankDraft = () => ({
  text: "",
  options: [
    { text: "", isCorrect: true },
    { text: "", isCorrect: false },
    { text: "", isCorrect: false },
  ] as OptionDraft[],
});

export default function AdminTestsPage() {
  const [tests, setTests] = useState<TestItem[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [detail, setDetail] = useState<Course | null>(null);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("ai");
  const [title, setTitle] = useState("");
  const [passPercentage, setPassPercentage] = useState(70);
  const [attempts, setAttempts] = useState(3);
  const [courseId, setCourseId] = useState("");
  const [scope, setScope] = useState<Scope>("lesson");
  const [moduleId, setModuleId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [lessonText, setLessonText] = useState("");
  const [sourceNote, setSourceNote] = useState("");
  const [generated, setGenerated] = useState<QuestionDraft[]>([]);
  const [manual, setManual] = useState<QuestionDraft[]>([]);
  const [draft, setDraft] = useState(blankDraft);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api<TestItem[]>("/api/v1/admin/tests").then(setTests).catch(() => setTests([]));
    api<Course[]>("/api/v1/admin/courses").then(setCourses).catch(() => setCourses([]));
  }, []);

  useEffect(() => {
    if (!courseId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    api<Course>(`/api/v1/courses/${courseId}`)
      .then((course) => {
        if (!cancelled) setDetail(course);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      });
    return () => {
      cancelled = true;
    };
  }, [courseId]);

  const selected = detail && detail.id === courseId
    ? detail
    : courses.find((course) => course.id === courseId) || null;
  const modules = selected?.modules || [];
  const selectedModule = modules.find((item) => item.id === moduleId) || null;
  const lessons = selectedModule?.lessons || [];

  useEffect(() => {
    if (mode !== "ai" || !detail || detail.id !== courseId) return;
    const mod = detail.modules.find((item) => item.id === moduleId);
    if (!mod) return;
    if (scope === "lesson") {
      setLessonText(mod.lessons.find((item) => item.id === lessonId)?.content || "");
      return;
    }
    setLessonText(mod.lessons.map((lesson) => lesson.content).filter(Boolean).join("\n\n"));
  }, [mode, scope, courseId, moduleId, lessonId, detail]);

  const placeLabel = useMemo(() => {
    const parts = [selected?.title, selectedModule?.title];
    if (scope === "lesson") {
      parts.push(lessons.find((item) => item.id === lessonId)?.title);
    }
    return parts.filter(Boolean).join(" · ");
  }, [selected, selectedModule, lessons, scope, lessonId]);

  function resetBuilder() {
    setTitle("");
    setPassPercentage(70);
    setAttempts(3);
    setCourseId("");
    setModuleId("");
    setLessonId("");
    setScope("lesson");
    setLessonText("");
    setGenerated([]);
    setManual([]);
    setDraft(blankDraft());
    setSourceNote("");
    setError("");
  }

  function targetBody() {
    if (title.trim().length < 3) throw new Error("Test nomi kamida 3 ta belgi bo'lsin");
    if (!courseId || !moduleId) throw new Error("Kurs va modulni tanlang");
    if (scope === "lesson" && !lessonId) throw new Error("Darsni tanlang");
    return {
      title: title.trim(),
      description: placeLabel,
      passPercentage,
      totalAttemptsAllowed: attempts,
      courseId,
      moduleId,
      lessonId: scope === "lesson" ? lessonId : undefined,
      scope,
    };
  }

  async function handleGenerate() {
    setError("");
    if (lessonText.trim().length < 10) {
      setError("Dars matni qisqa. Darsni tanlang yoki matnni kiriting.");
      return;
    }
    setGenerating(true);
    try {
      const payload = await api<{
        source: string;
        questions: { text: string; options: OptionDraft[] }[];
      }>("/api/v1/admin/tests/generate", {
        method: "POST",
        body: JSON.stringify({ text: lessonText }),
      });
      setGenerated(
        payload.questions.map((question, index) => ({
          id: `g-${Date.now()}-${index}`,
          text: question.text,
          options: question.options,
        }))
      );
      setSourceNote(
        payload.source === "ai"
          ? "Savollar AI orqali tuzildi. Saqlashdan oldin ko'rib chiqing."
          : "AI kaliti yo'q, shu sabab matndan andoza savollar tuzildi."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Savol yaratilmadi");
    } finally {
      setGenerating(false);
    }
  }

  function addManualQuestion() {
    setError("");
    const text = draft.text.trim();
    const options = draft.options
      .map((option) => ({ text: option.text.trim(), isCorrect: option.isCorrect }))
      .filter((option) => option.text);
    const correct = options.filter((option) => option.isCorrect).length;
    if (text.length < 3) {
      setError("Savol matni kamida 3 ta belgi bo'lsin");
      return;
    }
    if (options.length < 2 || correct !== 1) {
      setError("Kamida ikkita variant kiriting va bittasini to'g'ri deb belgilang");
      return;
    }
    setManual((prev) => [...prev, { id: `m-${Date.now()}`, text, options }]);
    setDraft(blankDraft());
  }

  async function handleSave(questions: QuestionDraft[]) {
    setError("");
    setSaving(true);
    try {
      const created = await api<TestItem>("/api/v1/admin/tests", {
        method: "POST",
        body: JSON.stringify({
          ...targetBody(),
          questions: questions.map((question) => ({
            text: question.text,
            options: question.options,
          })),
        }),
      });
      setTests((prev) => [created, ...prev]);
      setOpen(false);
      resetBuilder();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Test saqlanmadi");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">Testlar</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Test AI orqali yoki qo&apos;lda, bitta-bitta savol bilan tuziladi va modul yoki darsga biriktiriladi
          </p>
        </div>
        <button
          onClick={() => {
            setOpen((value) => !value);
            setError("");
          }}
          className="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold shadow-md flex items-center space-x-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>{open ? "Yopish" : "Yangi test"}</span>
        </button>
      </div>

      {open && (
        <div className="bg-card border border-border/70 rounded-3xl p-4 sm:p-6 shadow-sm space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setMode("ai")}
              className={`rounded-2xl border px-4 py-3 text-left ${
                mode === "ai" ? "border-purple-500 bg-purple-500/10" : "border-border/70"
              }`}
            >
              <span className="flex items-center gap-2 text-sm font-bold">
                <Sparkles className="w-4 h-4 text-purple-400" />
                AI orqali
              </span>
              <span className="mt-1 block text-[11px] text-muted-foreground">
                Tanlangan dars matnidan savollar tuziladi
              </span>
            </button>
            <button
              type="button"
              onClick={() => setMode("manual")}
              className={`rounded-2xl border px-4 py-3 text-left ${
                mode === "manual" ? "border-primary bg-primary/10" : "border-border/70"
              }`}
            >
              <span className="flex items-center gap-2 text-sm font-bold">
                <PenLine className="w-4 h-4 text-primary" />
                Qo&apos;lda
              </span>
              <span className="mt-1 block text-[11px] text-muted-foreground">
                Savollar bittadan qo&apos;shiladi, so&apos;ng test saqlanadi
              </span>
            </button>
          </div>

          {courses.length === 0 && (
            <p className="text-xs text-amber-500">
              Hali kurs yo&apos;q. Avval{" "}
              <Link href="/admin/courses/new" className="underline font-semibold">
                kurs va dars
              </Link>{" "}
              yarating, keyin testni shu darsga ulang.
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <label className="sm:col-span-2 space-y-1.5">
              <span className="font-semibold">Test nomi</span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Masalan: 1-dars bo'yicha nazorat"
                className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
              />
            </label>
            <label className="space-y-1.5">
              <span className="font-semibold">O&apos;tish bali, %</span>
              <input
                type="number"
                min={1}
                max={100}
                value={passPercentage}
                onChange={(event) => setPassPercentage(Number(event.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
              />
            </label>
            <label className="space-y-1.5">
              <span className="font-semibold">Urinishlar soni</span>
              <input
                type="number"
                min={1}
                value={attempts}
                onChange={(event) => setAttempts(Number(event.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
              />
            </label>
            <label className="space-y-1.5">
              <span className="font-semibold">Kurs</span>
              <select
                value={courseId}
                onChange={(event) => {
                  setCourseId(event.target.value);
                  setModuleId("");
                  setLessonId("");
                }}
                className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
              >
                <option value="">Kursni tanlang</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1.5">
              <span className="font-semibold">Biriktirish</span>
              <select
                value={scope}
                onChange={(event) => setScope(event.target.value as Scope)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
              >
                <option value="lesson">Kurs darsi</option>
                <option value="module">Modul</option>
              </select>
            </label>
            <label className="space-y-1.5">
              <span className="font-semibold">Modul</span>
              <select
                value={moduleId}
                onChange={(event) => {
                  setModuleId(event.target.value);
                  setLessonId("");
                }}
                className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
              >
                <option value="">Modulni tanlang</option>
                {modules.map((module) => (
                  <option key={module.id} value={module.id}>
                    {module.title}
                  </option>
                ))}
              </select>
            </label>
            {scope === "lesson" && (
              <label className="space-y-1.5">
                <span className="font-semibold">Dars</span>
                <select
                  value={lessonId}
                  onChange={(event) => setLessonId(event.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60"
                >
                  <option value="">Darsni tanlang</option>
                  {lessons.map((lesson) => (
                    <option key={lesson.id} value={lesson.id}>
                      {lesson.title}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>

          {placeLabel && (
            <p className="text-[11px] text-muted-foreground">Biriktiriladi: {placeLabel}</p>
          )}

          {mode === "ai" ? (
            <div className="space-y-3 rounded-2xl border border-purple-500/30 bg-purple-950/20 p-4">
              <textarea
                rows={5}
                value={lessonText}
                onChange={(event) => setLessonText(event.target.value)}
                placeholder="Dars matni shu yerga tushadi yoki o'zingiz yozing"
                className="w-full p-3 rounded-2xl bg-secondary/60 border border-border/70 text-xs"
              />
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <span className="text-[11px] text-muted-foreground">{sourceNote}</span>
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={generating}
                  className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-bold disabled:opacity-50"
                >
                  {generating ? "Tuzilmoqda..." : "Savollarni tuzish"}
                </button>
              </div>
              <QuestionList
                questions={generated}
                onRemove={(id) => setGenerated((prev) => prev.filter((item) => item.id !== id))}
              />
              {generated.length > 0 && (
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => handleSave(generated)}
                  className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold inline-flex items-center gap-1 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Testni saqlash
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4 rounded-2xl border border-border/70 p-4">
              <div className="space-y-2">
                <label className="block text-xs font-semibold">
                  {manual.length + 1}-savol
                  <input
                    value={draft.text}
                    onChange={(event) => setDraft((prev) => ({ ...prev, text: event.target.value }))}
                    placeholder="Savol matnini yozing"
                    className="mt-1.5 w-full px-3.5 py-2.5 rounded-xl bg-secondary/60 border border-border/60 font-normal"
                  />
                </label>
                <div className="space-y-2">
                  {draft.options.map((option, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="correct-option"
                        checked={option.isCorrect}
                        onChange={() =>
                          setDraft((prev) => ({
                            ...prev,
                            options: prev.options.map((item, itemIndex) => ({
                              ...item,
                              isCorrect: itemIndex === index,
                            })),
                          }))
                        }
                        aria-label="To'g'ri javob"
                      />
                      <input
                        value={option.text}
                        onChange={(event) =>
                          setDraft((prev) => ({
                            ...prev,
                            options: prev.options.map((item, itemIndex) =>
                              itemIndex === index ? { ...item, text: event.target.value } : item
                            ),
                          }))
                        }
                        placeholder={`${index + 1}-variant`}
                        className="flex-1 px-3 py-2 rounded-xl bg-secondary/60 border border-border/60 text-xs"
                      />
                      {draft.options.length > 2 && (
                        <button
                          type="button"
                          onClick={() =>
                            setDraft((prev) => {
                              const options = prev.options.filter((_, itemIndex) => itemIndex !== index);
                              if (!options.some((item) => item.isCorrect) && options[0]) {
                                options[0] = { ...options[0], isCorrect: true };
                              }
                              return { ...prev, options };
                            })
                          }
                          className="text-red-500"
                          aria-label="Variantni olib tashlash"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      setDraft((prev) => ({
                        ...prev,
                        options: [...prev.options, { text: "", isCorrect: false }],
                      }))
                    }
                    className="px-3 py-2 rounded-xl border border-border/70 text-xs font-semibold"
                  >
                    Variant qo&apos;shish
                  </button>
                  <button
                    type="button"
                    onClick={addManualQuestion}
                    className="px-3 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold"
                  >
                    Shu savolni qo&apos;shish
                  </button>
                </div>
              </div>
              <QuestionList
                questions={manual}
                onRemove={(id) => setManual((prev) => prev.filter((item) => item.id !== id))}
              />
              <button
                type="button"
                disabled={saving || manual.length === 0}
                onClick={() => handleSave(manual)}
                className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold disabled:opacity-50 inline-flex items-center gap-1"
              >
                <CheckCircle2 className="w-4 h-4" />
                Testni tayyorlash ({manual.length} savol)
              </button>
            </div>
          )}

          {error && <p className="text-xs font-semibold text-red-500">{error}</p>}
        </div>
      )}

      <div className="bg-card border border-border/70 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-xs">
            <thead className="bg-secondary/60 text-muted-foreground border-b border-border/60">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Test nomi</th>
                <th className="py-3.5 px-4 font-semibold">Modul / dars</th>
                <th className="py-3.5 px-4 font-semibold">Savollar</th>
                <th className="py-3.5 px-4 font-semibold">Vaqt</th>
                <th className="py-3.5 px-4 font-semibold">O&apos;tish bali</th>
                <th className="py-3.5 px-4 font-semibold text-right">Amal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              {tests.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 px-4 text-center text-muted-foreground">
                    Hozircha test yo&apos;q.
                  </td>
                </tr>
              )}
              {tests.map((test) => (
                <tr key={test.id} className="hover:bg-secondary/20">
                  <td className="py-4 px-4 font-bold text-foreground">{test.title}</td>
                  <td className="py-4 px-4 text-muted-foreground">
                    {[test.courseTitle, test.moduleTitle, test.lessonTitle].filter(Boolean).join(" · ") ||
                      "Biriktirilmagan"}
                  </td>
                  <td className="py-4 px-4 font-semibold">{test.questionsCount} ta</td>
                  <td className="py-4 px-4 text-muted-foreground">{test.durationMinutes} daqiqa</td>
                  <td className="py-4 px-4 font-bold text-emerald-500">{test.passPercentage}%</td>
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => {
                        if (!confirm("Ushbu testni o'chirishni xohlaysizmi?")) return;
                        api(`/api/v1/admin/tests/${test.id}`, { method: "DELETE" })
                          .then(() => setTests((prev) => prev.filter((item) => item.id !== test.id)))
                          .catch((err: Error) => alert(err.message));
                      }}
                      className="p-1.5 rounded-lg bg-red-500/10 text-red-500"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
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

function QuestionList({
  questions,
  onRemove,
}: {
  questions: QuestionDraft[];
  onRemove: (id: string) => void;
}) {
  if (questions.length === 0) return null;
  return (
    <div className="space-y-2">
      {questions.map((question, index) => (
        <div key={question.id} className="rounded-2xl border border-border/70 p-3 space-y-1.5">
          <div className="flex items-start justify-between gap-2">
            <p className="text-xs font-bold">
              {index + 1}. {question.text}
            </p>
            <button type="button" onClick={() => onRemove(question.id)} className="text-red-500 shrink-0">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
          {question.options.map((option, optionIndex) => (
            <p
              key={optionIndex}
              className={`text-[11px] ${option.isCorrect ? "text-emerald-500 font-semibold" : "text-muted-foreground"}`}
            >
              {option.isCorrect ? "To'g'ri: " : "Variant: "}
              {option.text}
            </p>
          ))}
        </div>
      ))}
    </div>
  );
}
