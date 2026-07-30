import type { NextConfig } from "next";
import { loadEnvConfig } from "@next/env";
import path from "node:path";

// Load the shared repo-root `.env` (also used by the Python back-end).
loadEnvConfig(path.resolve("frontend", ".."));

const nextConfig: NextConfig = {
    /* config options here */
};

export default nextConfig;
