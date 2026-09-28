import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/**
 * Resolve the FastAPI origin from process env at request time so Docker/runtime
 * overrides of BACKEND_HOST / BACKEND_PORT work without rebuilding the image.
 */
function backendOrigin(): string {
    const host = (process.env["BACKEND_HOST"] ?? "").trim();
    const port = (process.env["BACKEND_PORT"] ?? "").trim();
    if (!host || !port) {
        throw new Error(
            "BACKEND_HOST and BACKEND_PORT must be set (see .env.template)",
        );
    }
    // 0.0.0.0 is a bind-all address; Next.js must connect via loopback.
    const connectHost = host === "0.0.0.0" ? "127.0.0.1" : host;
    return `http://${connectHost}:${port}`;
}

export function proxy(request: NextRequest) {
    const pathname = request.nextUrl.pathname;
    const backendPath = pathname.replace(/^\/api/, "") || "/";
    const destination = new URL(
        `${backendPath}${request.nextUrl.search}`,
        backendOrigin(),
    );
    return NextResponse.rewrite(destination);
}

export const config = {
    matcher: "/api/:path*",
};
