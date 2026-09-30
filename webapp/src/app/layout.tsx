import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { SessionProvider } from "@/lib/session";
import { TelegramBoot } from "@/components/TelegramBoot";

export const metadata: Metadata = {
  title: "IIV EduBot | Ta'lim Platformasi",
  description: "O'zbekiston Respublikasi IIV Akademiyasi va sohaviy xodimlar uchun zamonaviy o'quv platformasi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className="dark">
      <head>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"
        />
      </head>
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
        <SessionProvider>
          <TelegramBoot />
          {children}
        </SessionProvider>
      </body>
    </html>
  );
}
