import { NextRequest, NextResponse } from "next/server";

const TARGET = process.env.API_PROXY_URL || "http://127.0.0.1:8081";

async function proxy(request: NextRequest, path: string[]) {
  const url = `${TARGET}/${path.join("/")}${request.nextUrl.search}`;
  const headers = new Headers();
  const authorization = request.headers.get("authorization");
  const contentType = request.headers.get("content-type");
  if (authorization) headers.set("authorization", authorization);
  if (contentType) headers.set("content-type", contentType);

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
    });
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Web API ishlamayapti. python -m bot.api.server ni ishga tushiring." },
      { status: 503 }
    );
  }
}

type Ctx = { params: { path: string[] } };

export async function GET(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path);
}
export async function POST(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path);
}
export async function DELETE(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path);
}
export async function PUT(request: NextRequest, ctx: Ctx) {
  return proxy(request, ctx.params.path);
}
