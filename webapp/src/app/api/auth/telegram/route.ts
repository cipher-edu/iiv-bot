import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  try {
    const { initData } = await req.json();

    if (!initData) {
      return NextResponse.json({ error: "initData mavjud emas" }, { status: 400 });
    }

    const botToken = process.env.BOT_TOKEN || "";

    // Parse initData query string
    const urlParams = new URLSearchParams(initData);
    const hash = urlParams.get("hash");
    urlParams.delete("hash");

    // Sort keys alphabetically
    const paramsList: string[] = [];
    Array.from(urlParams.keys())
      .sort()
      .forEach((key) => {
        paramsList.push(`${key}=${urlParams.get(key)}`);
      });

    const dataCheckString = paramsList.join("\n");

    // In production, verify HMAC-SHA256 with botToken
    if (botToken) {
      const secretKey = crypto
        .createHmac("sha256", "WebAppData")
        .update(botToken)
        .digest();

      const calculatedHash = crypto
        .createHmac("sha256", secretKey)
        .update(dataCheckString)
        .digest("hex");

      if (calculatedHash !== hash) {
        return NextResponse.json(
          { error: "Autentifikatsiya xatosi: Ma'lumotlar soxtalashtirilgan" },
          { status: 401 }
        );
      }
    }

    // Extract user JSON
    const userStr = urlParams.get("user");
    const user = userStr ? JSON.parse(userStr) : null;

    return NextResponse.json({
      success: true,
      user,
      message: "Foydalanuvchi muvaffaqiyatli autentifikatsiyadan o'tdi",
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Server xatosi: " + err.message },
      { status: 500 }
    );
  }
}
