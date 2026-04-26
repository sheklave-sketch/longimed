import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const LANDING_HOSTS = new Set(["longimed.com", "www.longimed.com"]);

export function middleware(request: NextRequest) {
  const host = (request.headers.get("host") || "").toLowerCase();
  const path = request.nextUrl.pathname;
  const isPublic = LANDING_HOSTS.has(host);

  if (isPublic && path === "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/landing";
    return NextResponse.redirect(url, 308);
  }

  // On the public domain, /doctors is the marketing directory (rewrite, not redirect).
  // On the Telegram Mini App URL, /doctors keeps its existing in-app behavior.
  if (isPublic && path === "/doctors") {
    const url = request.nextUrl.clone();
    url.pathname = "/doctors-public";
    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/doctors"],
};
