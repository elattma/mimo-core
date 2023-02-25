import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export const middleware = (req: NextRequest) => {
  // See https://github.com/vercel/platforms/blob/main/middleware.ts for more
  // details on this implementation.

  const url = req.nextUrl;
  const hostname = req.headers.get("host") || "";
  const pathname = url.pathname;

  const currentHost =
    process.env.NODE_ENV === "production"
      ? hostname.replace(".mimo.team", "")
      : hostname.replace(".localhost:3000", "");

  if (currentHost === "app") {
    if (url.pathname === "/login" && req.cookies.get("appSession")) {
      url.pathname = "/";
      return NextResponse.redirect(url);
    }

    url.pathname = `/app${url.pathname}`;
    return NextResponse.rewrite(url);
  }

  return NextResponse.rewrite(
    new URL(`/_sites/${currentHost}${pathname}`, req.url)
  );
};

export const config = {
  matcher: [
    /*
     * Match all paths except for:
     * 1. /api routes
     * 2. /_next (Next.js internals)
     * 3. all root files inside /public (e.g. /favicon.ico)
     */
    "/((?!api/|_next/|_static/|[\\w-]+\\.\\w+).*)",
  ],
};
