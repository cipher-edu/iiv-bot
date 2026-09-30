import { NextResponse } from "next/server";
import { coursesMock } from "@/lib/data";

export async function GET() {
  return NextResponse.json({
    success: true,
    courses: coursesMock,
  });
}
