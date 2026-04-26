import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const LANDING_HOSTS = new Set(["longimed.com", "www.longimed.com"]);

export function middleware(request: NextRequest) {
  const host = (request.headers.get("host") || "").toLowerCase();

  if (LANDING_HOSTS.has(host) && request.nextUrl.pathname === "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/landing";
    return NextResponse.redirect(url, 308);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/"],
};
