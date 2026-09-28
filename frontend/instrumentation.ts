import type { Instrumentation } from "next";

export async function register() {
    if (process.env.NEXT_RUNTIME === "nodejs") {
        const { setupServerFileLogging } =
            await import("./lib/server-file-log");
        setupServerFileLogging();
    }
}

export const onRequestError: Instrumentation.onRequestError = async (
    error,
    request,
    context,
) => {
    if (process.env.NEXT_RUNTIME !== "nodejs") {
        return;
    }
    const { appendServerLogLine } = await import("./lib/server-file-log");

    // `Instrumentation.onRequestError` types `error` as `unknown`, so we must
    // narrow before accessing message/digest.
    const messagePart =
        error instanceof Error
            ? error.message
            : (typeof error === "object" && error !== null && "message" in error
              ? String((error as { message?: unknown }).message)
              : String(error));

    const digestPart =
        typeof error === "object" && error !== null && "digest" in error
            ? String((error as { digest?: unknown }).digest)
            : "unknown";

    const message =
        `${messagePart} [${digestPart}] ` +
        `${request.method} ${request.path} ` +
        `(${context.routerKind} ${context.routeType} ${context.routePath})`;
    appendServerLogLine("ERROR", "onRequestError", message);
};
