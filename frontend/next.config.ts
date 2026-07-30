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
const { combinedEnv } = loadEnvConfig(
    repoRoot,
    process.env.NODE_ENV !== "production",
    undefined,
    true,
);

const backendUrl = combinedEnv.NEXT_PUBLIC_BACKEND_URL;
if (!backendUrl) {
    throw new Error(
        "NEXT_PUBLIC_BACKEND_URL is missing from the repo-root .env (see .env.template)",
    );
}

const nextConfig: NextConfig = {
    // Explicitly expose to the client bundle; loadEnvConfig alone is not enough
    // for NEXT_PUBLIC_ inlining when the file lives outside frontend/.
    env: {
        NEXT_PUBLIC_BACKEND_URL: backendUrl,
    },
};

export default nextConfig;
