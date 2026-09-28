import type { NextConfig } from "next";
import { loadEnvConfig } from "@next/env";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);

// Next loads env from frontend/ first and caches an empty result. forceReload
// is required so the shared repo-root `.env` is actually read (see vercel/next.js#92040).
// Side effect: populates process.env for `next dev` / `next build` so proxy.ts
// can read BACKEND_HOST / BACKEND_PORT. Those are not baked into the build;
// Docker/runtime overrides apply when the standalone server starts.
loadEnvConfig(repoRoot, process.env.NODE_ENV !== "production", undefined, true);

const nextConfig: NextConfig = {
    output: "standalone",
};

export default nextConfig;
