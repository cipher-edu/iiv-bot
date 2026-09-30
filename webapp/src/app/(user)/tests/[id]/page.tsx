"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Clock, CheckCircle2, XCircle, Award, RotateCcw } from "lucide-react";
import { TestItem } from "@/types";
import { api } from "@/lib/api";
import { triggerHaptic } from "@/lib/telegram";
import { useSession } from "@/lib/session";

export default function TestPlayerPage() {
  const params = useParams();
  const testId = params?.id as string;
  const { refresh } = useSession();
  const [test, setTest] = useState<TestItem | null>(null);
  const [loadError, setLoadError] = useState("");
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverResult, setServerResult] = useState<{
    correctCount: number;
    percentage: number;
    isPassed: boolean;
    pointsAwarded: number;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<TestItem>(`/api/v1/tests/${testId}`)
      .then((payload) => {
        if (cancelled) return;
        setTest(payload);
        setTimeLeft(payload.durationMinutes * 60);
      })
      .catch((err: Error) => {
        if (!cancelled) setLoadError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [testId]);

  useEffect(() => {
    if (!test || isFinished || timeLeft <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [test, isFinished, timeLeft <= 0]);

  const answersRef = useRef(selectedAnswers);
  answersRef.current = selectedAnswers;
  const startedRef = useRef(false);
  const finishingRef = useRef(false);

  useEffect(() => {
    if (!test || timeLeft <= 0 || isFinished) return;
    startedRef.current = true;
  }, [test, timeLeft, isFinished]);

  useEffect(() => {
    if (!test || !startedRef.current || timeLeft !== 0 || isFinished || finishingRef.current) return;
    finishingRef.current = true;
    setSubmitting(true);
    void (async () => {
      try {
        const result = await api<{
          correctCount: number;
          percentage: number;
          isPassed: boolean;
          pointsAwarded: number;
        }>(`/api/v1/tests/${test.id}/finish`, {
          method: "POST",
          body: JSON.stringify({
            answers: Object.entries(answersRef.current).map(([questionId, optionId]) => ({
              questionId,
              optionId,
            })),
          }),
        });
        setServerResult(result);
        setIsFinished(true);
        triggerHaptic("success");
        await refresh();
      } catch {
        finishingRef.current = false;
        triggerHaptic("error");
      } finally {
        setSubmitting(false);
      }
    })();
  }, [timeLeft, isFinished, test, refresh]);

  if (!test) {
    return <p className="text-sm text-muted-foreground">{loadError || "Test yuklanmoqda..."}</p>;
  }

  const questions = test.questions;
  if (questions.length === 0) {
    return <p className="text-sm text-muted-foreground">Bu testda savol yo&apos;q.</p>;
  }
  const currentQuestion = questions[currentIdx];

  const handleSelectOption = (optionId: string) => {
    triggerHaptic("light");
    setSelectedAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: optionId,
    }));
  };

  const submitTest = async () => {
    setSubmitting(true);
    try {
      const result = await api<{
        correctCount: number;
        percentage: number;
        isPassed: boolean;
        pointsAwarded: number;
      }>(`/api/v1/tests/${test.id}/finish`, {
        method: "POST",
        body: JSON.stringify({
          answers: Object.entries(selectedAnswers).map(([questionId, optionId]) => ({
            questionId,
            optionId,
          })),
        }),
      });
      setServerResult(result);
      setIsFinished(true);
      triggerHaptic("success");
      await refresh();
    } catch {
      triggerHaptic("error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    triggerHaptic("light");
    if (currentIdx < questions.length - 1) {
      setCurrentIdx((prev) => prev + 1);
    } else {
      void submitTest();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  const result = isFinished ? serverResult : null;

  return (
    <div className="space-y-4 -mt-2">
      {/* Top Header & Timer */}
      <div className="flex items-center justify-between py-1">
        <Link
          href="/tests"
          onClick={() => triggerHaptic("light")}
          className="flex items-center space-x-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Testlar ro&apos;yxati</span>
        </Link>

        {!isFinished && (
          <div
            className={`flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold border ${
              timeLeft < 120
                ? "bg-red-500/10 text-red-500 border-red-500/30 animate-pulse"
                : "bg-secondary text-foreground border-border/40"
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>{formatTime(timeLeft)}</span>
          </div>
        )}
      </div>

      {!isFinished ? (
        <div className="space-y-4">
          {/* Progress Indicators */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-muted-foreground font-medium">
              <span>
                Savol: <strong className="text-foreground">{currentIdx + 1}</strong> / {questions.length}
              </span>
              <span>{Math.round(((currentIdx + 1) / questions.length) * 100)}%</span>
            </div>
            <div className="flex space-x-1.5">
              {questions.map((q, idx) => {
                const isAnswered = selectedAnswers[q.id] !== undefined;
                const isCurrent = idx === currentIdx;

                return (
                  <button
                    key={q.id}
                    onClick={() => {
                      triggerHaptic("light");
                      setCurrentIdx(idx);
                    }}
                    className={`h-1.5 flex-1 rounded-full transition-all ${
                      isCurrent
                        ? "bg-primary ring-2 ring-primary/40"
                        : isAnswered
                        ? "bg-primary/80"
                        : "bg-secondary"
                    }`}
                  />
                );
              })}
            </div>
          </div>

          {/* Question Card */}
          <div className="bg-card border border-border/70 rounded-2xl p-5 shadow-sm space-y-4">
            <h3 className="font-bold text-base text-foreground leading-snug">
              {currentQuestion?.text}
            </h3>

            {/* Options */}
            <div className="space-y-2.5">
              {currentQuestion?.options.map((option) => {
                const isSelected = selectedAnswers[currentQuestion.id] === option.id;

                return (
                  <button
                    key={option.id}
                    onClick={() => handleSelectOption(option.id)}
                    className={`w-full p-3.5 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                      isSelected
                        ? "bg-primary/10 border-primary text-primary shadow-sm"
                        : "bg-secondary/40 border-border/60 text-foreground hover:bg-secondary/70"
                    }`}
                  >
                    <span>{option.text}</span>
                    <span
                      className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 ml-2 ${
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-card"
                      }`}
                    >
                      {isSelected && <span className="w-1.5 h-1.5 bg-white rounded-full" />}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Action Navigation */}
          <div className="flex justify-between items-center pt-2">
            <button
              disabled={currentIdx === 0}
              onClick={() => {
                triggerHaptic("light");
                setCurrentIdx((p) => p - 1);
              }}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-muted-foreground hover:text-foreground disabled:opacity-40 transition-colors"
            >
              Oldingisi
            </button>

            <button
              onClick={handleNext}
              disabled={submitting}
              className="px-6 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-bold shadow-md transition-transform active:scale-95 disabled:opacity-60"
            >
              {submitting
                ? "Tekshirilmoqda..."
                : currentIdx === questions.length - 1
                  ? "Testni yakunlash"
                  : "Keyingisi"}
            </button>
          </div>
        </div>
      ) : (
        /* Results View */
        <div className="bg-card border border-border/70 rounded-3xl p-6 shadow-lg text-center space-y-5 animate-in fade-in zoom-in-95 duration-200">
          <div
            className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto border-4 shadow-inner ${
              result?.isPassed
                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/40"
                : "bg-red-500/10 text-red-500 border-red-500/40"
            }`}
          >
            {result?.isPassed ? (
              <CheckCircle2 className="w-10 h-10" />
            ) : (
              <XCircle className="w-10 h-10" />
            )}
          </div>

          <div className="space-y-1">
            <span
              className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full ${
                result?.isPassed
                  ? "bg-emerald-500/15 text-emerald-500"
                  : "bg-red-500/15 text-red-500"
              }`}
            >
              {result?.isPassed ? "Muvaffaqiyatli topshirildi!" : "O'tish baliga yetmadi"}
            </span>
            <h2 className="text-3xl font-black text-foreground pt-2">
              {result?.percentage}%
            </h2>
            <p className="text-xs text-muted-foreground">
              To&apos;g&apos;ri javoblar: {result?.correctCount} ta (jami {questions.length} tadan)
            </p>
          </div>

          {result?.isPassed && (
            <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center space-x-2 text-xs font-semibold">
              <Award className="w-4 h-4" />
              <span>+{result?.pointsAwarded || 0} ball yozildi</span>
            </div>
          )}

          <div className="pt-2 flex flex-col space-y-2">
            <Link
              href="/profile"
              className="w-full py-3 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-bold text-xs shadow-md transition-transform active:scale-95"
            >
              Profilga o&apos;tish
            </Link>

            <button
              onClick={() => {
                triggerHaptic("medium");
                setSelectedAnswers({});
                setServerResult(null);
                setTimeLeft(test.durationMinutes * 60);
                setCurrentIdx(0);
                finishingRef.current = false;
                setIsFinished(false);
              }}
              className="w-full py-2.5 rounded-xl border border-border/80 text-foreground text-xs font-semibold hover:bg-secondary transition-colors flex items-center justify-center space-x-1"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Qaytadan urinish</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
