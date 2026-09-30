"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, RefreshCw } from "lucide-react";
import { triggerHaptic } from "@/lib/telegram";
import { api } from "@/lib/api";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}

export default function AITutorPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "ai",
      text: "Assalomu alaykum! Men IIV EduBot sun'iy intellekt tyutoriman. Kurslar, darslar, qonunchilik yoki testlarga tayyorgarlik bo'yicha istalgan savolingizni berishingiz mumkin.",
      timestamp: "09:00",
    },
  ]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    "Kiberxavfsizlik bo'yicha asosiy xatolar qaysilar?",
    "Ikki bosqichli autentifikatsiya (2FA) nima?",
    "Testga tayyorgarlik uchun 3 ta savol tuzib ber",
    "Fishing (Phishing) hujumidan qanday saqlanish kerak?",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isLoading) return;

    triggerHaptic("medium");
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    api<{ reply: string }>("/api/v1/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message: text.trim() }),
    })
      .then((payload) => {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            text: payload.reply,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
        triggerHaptic("light");
      })
      .catch((err: Error) => {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            text: err.message || "Javob olinmadi",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
      })
      .finally(() => setIsLoading(false));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-135px)] -mt-2">
      {/* Header */}
      <div className="flex items-center space-x-2.5 pb-3 border-b border-border/50 shrink-0">
        <div className="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
          <Bot className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-foreground flex items-center space-x-1.5">
            <span>AI Tyutor</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </h2>
          <p className="text-[10px] text-muted-foreground">Claude / GPT o&apos;quv yordamchisi</p>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start space-x-2 ${
              m.sender === "user" ? "flex-row-reverse space-x-reverse" : ""
            }`}
          >
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                m.sender === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-purple-600/20 text-purple-400 border border-purple-500/30"
              }`}
            >
              {m.sender === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>

            <div
              className={`max-w-[82%] rounded-2xl p-3 text-xs leading-relaxed space-y-1 ${
                m.sender === "user"
                  ? "bg-primary text-primary-foreground rounded-tr-none shadow-sm"
                  : "bg-card border border-border/70 text-foreground rounded-tl-none shadow-sm"
              }`}
            >
              <p className="whitespace-pre-line">{m.text}</p>
              <span
                className={`text-[9px] block text-right font-medium ${
                  m.sender === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                }`}
              >
                {m.timestamp}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/30">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-card border border-border/70 rounded-2xl rounded-tl-none px-3.5 py-2.5 shadow-sm flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" />
              <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Chips */}
      {messages.length <= 2 && (
        <div className="py-2 overflow-x-auto flex space-x-1.5 scrollbar-none shrink-0">
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p)}
              className="px-2.5 py-1 rounded-full bg-secondary/80 hover:bg-secondary text-foreground text-[11px] whitespace-nowrap border border-border/50 shrink-0 transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="pt-2 border-t border-border/50 shrink-0 flex items-center space-x-2">
        <input
          type="text"
          placeholder="Savolingizni yozing..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="flex-1 px-3.5 py-2.5 rounded-xl bg-card border border-border/70 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/40 focus:border-purple-500 transition-all"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || isLoading}
          className="w-10 h-10 rounded-xl bg-purple-600 hover:bg-purple-500 text-white flex items-center justify-center shrink-0 disabled:opacity-40 shadow-sm transition-transform active:scale-95"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
