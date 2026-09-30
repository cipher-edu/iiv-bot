"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { getTelegramWebApp } from "@/lib/telegram";

export function TelegramBoot() {
  const pathname = usePathname();

  useEffect(() => {
    const tg = getTelegramWebApp();
    if (!tg) return;
    tg.ready();
    tg.expand();
    const root = document.documentElement;
    root.classList.toggle("dark", tg.colorScheme !== "light");
    const theme = tg.themeParams || {};
    if (theme.bg_color) root.style.setProperty("--tg-theme-bg-color", theme.bg_color);
    if (theme.text_color) root.style.setProperty("--tg-theme-text-color", theme.text_color);
    const app = tg as typeof tg & {
      setHeaderColor?: (color: string) => void;
      setBackgroundColor?: (color: string) => void;
    };
    try {
      app.setHeaderColor?.("secondary_bg_color");
      app.setBackgroundColor?.(theme.bg_color || "bg_color");
    } catch {
      /* older Telegram clients */
    }
  }, []);

  useEffect(() => {
    const tg = getTelegramWebApp();
    if (!tg?.BackButton) return;
    const onBack = () => window.history.back();
    if (pathname && pathname !== "/") {
      tg.BackButton.show();
      tg.BackButton.onClick(onBack);
    } else {
      tg.BackButton.hide();
    }
    return () => tg.BackButton.offClick(onBack);
  }, [pathname]);

  return null;
}
