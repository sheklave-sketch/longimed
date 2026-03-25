import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://31.97.47.190:8000";

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetPath = "/" + path.join("/");
  const url = `${BACKEND_URL}${targetPath}${request.nextUrl.search}`;

  try {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({ error: "Backend unreachable", detail: String(err) }, { status: 502 });
  }
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetPath = "/" + path.join("/");
  const url = `${BACKEND_URL}${targetPath}`;

  try {
    const body = await request.json();
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({ error: "Backend unreachable", detail: String(err) }, { status: 502 });
  }
}
