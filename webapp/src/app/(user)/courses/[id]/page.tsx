"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Play, CheckCircle, FileText, Download, Star, Share2, Award } from "lucide-react";
import { Course } from "@/types";
import { api } from "@/lib/api";
import { triggerHaptic } from "@/lib/telegram";
import { useSession } from "@/lib/session";

export default function CourseDetailPage() {
  const params = useParams();
  const courseId = params?.id as string;
  const { refresh } = useSession();
  const [course, setCourse] = useState<Course | null>(null);
  const [loadError, setLoadError] = useState("");
  const [activeLessonId, setActiveLessonId] = useState<string>("");
  const [completedLessons, setCompletedLessons] = useState<Record<string, boolean>>({});
  const [showRatingModal, setShowRatingModal] = useState<boolean>(false);
  const [rating, setRating] = useState<number>(5);
  const [awarded, setAwarded] = useState(0);
  const [courseCompleted, setCourseCompleted] = useState(false);
  const [savingRating, setSavingRating] = useState(false);
  const [ratingSaved, setRatingSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api<Course>(`/api/v1/courses/${courseId}`)
      .then((payload) => {
        if (cancelled) return;
        setCourse(payload);
        const done: Record<string, boolean> = {};
        payload.modules.forEach((module) =>
          module.lessons.forEach((lesson) => {
            if (lesson.isCompleted) done[lesson.id] = true;
          })
        );
        setCompletedLessons(done);
        const first = payload.modules.flatMap((module) => module.lessons)[0];
        setActiveLessonId(first?.id || "");
      })
      .catch((err: Error) => {
        if (!cancelled) setLoadError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [courseId]);

  if (!course) {
    return <p className="text-sm text-muted-foreground">{loadError || "Dars yuklanmoqda..."}</p>;
  }

  const allLessons = course.modules.flatMap((module) => module.lessons);
  const activeLesson = allLessons.find((lesson) => lesson.id === activeLessonId) || allLessons[0];

  const handleCompleteLesson = () => {
    triggerHaptic("success");
    setAwarded(0);
    setCourseCompleted(false);
    setRatingSaved(false);
    setShowRatingModal(true);
  };

  const confirmRating = async () => {
    if (ratingSaved) {
      setShowRatingModal(false);
      return;
    }
    setSavingRating(true);
    try {
      const result = await api<{ pointsAwarded: number; courseCompleted: boolean }>(
        `/api/v1/courses/${course.id}/lessons/${activeLessonId}/complete`,
        { method: "POST", body: JSON.stringify({ stars: rating }) }
      );
      setAwarded(result.pointsAwarded);
      setCourseCompleted(result.courseCompleted);
      setCompletedLessons((prev) => ({ ...prev, [activeLessonId]: true }));
      setRatingSaved(true);
      triggerHaptic("success");
      await refresh();
    } catch {
      triggerHaptic("error");
    } finally {
      setSavingRating(false);
    }
  };

  return (
    <div className="space-y-4 -mt-2">
      {/* Top Bar Navigation */}
      <div className="flex items-center justify-between py-1">
        <Link
          href="/courses"
          onClick={() => triggerHaptic("light")}
          className="flex items-center space-x-1 text-sm font-semibold text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Kurslar</span>
        </Link>
        <span className="text-xs bg-primary/10 text-primary px-2.5 py-1 rounded-full font-medium">
          {course.category}
        </span>
      </div>

      {(course.syllabusFiles || []).length > 0 && (
        <div className="bg-card border border-border/70 rounded-2xl p-4 space-y-2">
          <h2 className="text-sm font-bold text-foreground">Silabus fayllari</h2>
          {(course.syllabusFiles || []).map((file) => (
            <a
              key={file.id}
              href={file.url}
              download={file.title}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between gap-3 rounded-xl bg-secondary/50 px-3 py-2 text-xs font-semibold"
            >
              <span className="truncate">{file.title}</span>
              <Download className="w-4 h-4 shrink-0 text-primary" />
            </a>
          ))}
        </div>
      )}

      {/* Video / Content Display Card */}
      <div className="bg-card border border-border/70 rounded-2xl overflow-hidden shadow-sm">
        {activeLesson?.videoUrl ? (
          <div className="aspect-video w-full bg-black/90 relative flex items-center justify-center">
            <iframe
              src={activeLesson.videoUrl}
              title={activeLesson.title}
              className="w-full h-full border-0"
              allowFullScreen
            />
          </div>
        ) : (
          <div className="h-28 bg-gradient-to-r from-blue-900 to-indigo-950 p-4 flex flex-col justify-end text-white">
            <span className="text-[11px] font-medium text-blue-200 uppercase tracking-wider">
              Matnli dars
            </span>
            <h2 className="text-base font-bold line-clamp-1">{activeLesson?.title}</h2>
          </div>
        )}

        <div className="p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div className="space-y-0.5">
              <span className="text-[11px] text-primary font-semibold">
                Davomiyligi: {activeLesson?.durationMinutes} daqiqa
              </span>
              <h2 className="text-base font-bold text-foreground tracking-tight">
                {activeLesson?.title}
              </h2>
            </div>

            {completedLessons[activeLessonId] ? (
              <span className="flex items-center space-x-1 text-xs text-emerald-500 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full shrink-0">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Tugatilgan</span>
              </span>
            ) : (
              <button
                onClick={handleCompleteLesson}
                className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold px-3 py-1.5 rounded-xl shadow-sm transition-transform active:scale-95 shrink-0"
              >
                Yakunlash
              </button>
            )}
          </div>

          {/* Lesson Content Body */}
          <div className="text-xs text-foreground/90 leading-relaxed space-y-2 whitespace-pre-line border-t border-border/50 pt-3">
            {activeLesson?.content}
          </div>

          {/* Attachments Section */}
          {activeLesson?.attachments && activeLesson.attachments.length > 0 && (
            <div className="pt-3 border-t border-border/50 space-y-2">
              <span className="text-xs font-semibold text-foreground">Dars materiallari:</span>
              <div className="space-y-1.5">
                {activeLesson.attachments.map((att) => (
                  <div
                    key={att.id}
                    className="flex items-center justify-between p-2 rounded-xl bg-secondary/60 hover:bg-secondary border border-border/40 transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-primary" />
                      <div>
                        <p className="text-xs font-medium text-foreground">{att.title}</p>
                        <p className="text-[10px] text-muted-foreground">{att.size}</p>
                      </div>
                    </div>
                    <a
                      href={att.url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      onClick={() => triggerHaptic("light")}
                      className="p-1.5 rounded-lg bg-card text-foreground hover:bg-primary hover:text-primary-foreground transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Course Curriculum (Modules and Lessons) */}
      <div className="space-y-3 pt-2">
        <h3 className="font-bold text-base text-foreground">Kurs dasturi (Sillabus)</h3>

        <div className="space-y-3">
          {course.modules.map((module) => (
            <div
              key={module.id}
              className="bg-card border border-border/70 rounded-2xl p-3 shadow-sm space-y-2"
            >
              <h4 className="font-bold text-xs text-foreground uppercase tracking-wide px-1">
                {module.title}
              </h4>

              <div className="space-y-1">
                {module.lessons.map((lesson, idx) => {
                  const isActive = lesson.id === activeLessonId;
                  const isDone = completedLessons[lesson.id];

                  return (
                    <button
                      key={lesson.id}
                      onClick={() => {
                        triggerHaptic("light");
                        setActiveLessonId(lesson.id);
                      }}
                      className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left transition-all ${
                        isActive
                          ? "bg-primary text-primary-foreground shadow-sm font-semibold"
                          : "hover:bg-secondary/70 text-foreground"
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                            isActive
                              ? "bg-white/20 text-white"
                              : "bg-secondary text-muted-foreground font-semibold"
                          }`}
                        >
                          {idx + 1}
                        </span>
                        <div>
                          <p className="text-xs line-clamp-1">{lesson.title}</p>
                          <span
                            className={`text-[10px] ${
                              isActive ? "text-white/80" : "text-muted-foreground"
                            }`}
                          >
                            {lesson.durationMinutes} daqiqa
                          </span>
                        </div>
                      </div>

                      {isDone ? (
                        <CheckCircle
                          className={`w-4 h-4 ${
                            isActive ? "text-white" : "text-emerald-500"
                          }`}
                        />
                      ) : (
                        <Play
                          className={`w-3.5 h-3.5 ${
                            isActive ? "text-white fill-current" : "text-muted-foreground"
                          }`}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lesson Rating Modal */}
      {showRatingModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/80 rounded-3xl p-5 max-w-sm w-full text-center space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-500 flex items-center justify-center mx-auto">
              <Award className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h3 className="font-bold text-lg text-foreground">Darsni muvaffaqiyatli yakunladingiz!</h3>
              <p className="text-xs text-muted-foreground">
                {ratingSaved
                  ? `${awarded > 0 ? `+${awarded} ball yozildi. ` : ""}${courseCompleted ? "Kurs tugadi, sertifikat berildi." : "Bahoyingiz saqlandi."}`
                  : "Dars sifatini baholang:"}
              </p>
            </div>

            <div className="flex justify-center space-x-2 py-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => {
                    triggerHaptic("medium");
                    setRating(star);
                  }}
                  className="p-1 hover:scale-125 transition-transform"
                >
                  <Star
                    className={`w-8 h-8 ${
                      star <= rating ? "text-amber-400 fill-amber-400" : "text-muted-foreground/40"
                    }`}
                  />
                </button>
              ))}
            </div>

            <button
              onClick={confirmRating}
              disabled={savingRating}
              className="w-full py-3 rounded-2xl bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-sm shadow-md transition-all disabled:opacity-60"
            >
              {savingRating ? "Saqlanmoqda..." : ratingSaved ? "Davom etish" : "Bahoni tasdiqlash"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
