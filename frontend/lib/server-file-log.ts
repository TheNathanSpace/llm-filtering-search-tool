import { appendFileSync, existsSync } from "node:fs";
import path from "node:path";
import { formatWithOptions } from "node:util";

type ConsoleMethod = "debug" | "log" | "info" | "warn" | "error";

const LEVEL_RANK: Record<string, number> = {
    DEBUG: 10,
    INFO: 20,
    WARNING: 30,
    ERROR: 40,
    CRITICAL: 50,
};

const METHOD_LEVEL: Record<ConsoleMethod, string> = {
    debug: "DEBUG",
    log: "INFO",
    info: "INFO",
    warn: "WARNING",
    error: "ERROR",
};

const LOGGER_NAME = "frontend".padEnd(35);

let configured = false;

function padNumber(value: number, width = 2): string {
    return String(value).padStart(width, "0");
}

function resolveRepoRoot(): string {
    const cwd = process.cwd();
    if (
        existsSync(path.join(cwd, ".env")) ||
        existsSync(path.join(cwd, ".env.template"))
    ) {
        return cwd;
    }
    const parent = path.resolve(cwd, "..");
    if (
        existsSync(path.join(parent, ".env")) ||
        existsSync(path.join(parent, ".env.template"))
    ) {
        return parent;
    }
    return cwd;
}

function getLatestLogPath(): string | undefined {
    const dataDirectory = process.env.DATA_DIR?.trim();
    if (!dataDirectory) {
        return undefined;
    }
    return path.resolve(resolveRepoRoot(), dataDirectory, "logs", "latest.log");
}

function configuredLevelRank(): number {
    const name = (process.env.LOG_LEVEL ?? "DEBUG").trim().toUpperCase();
    return LEVEL_RANK[name] ?? LEVEL_RANK.DEBUG;
}

function formatTimestamp(date: Date): string {
    return (
        `${date.getFullYear()}-${padNumber(date.getMonth() + 1)}-${padNumber(date.getDate())} ` +
        `${padNumber(date.getHours())}:${padNumber(date.getMinutes())}:${padNumber(date.getSeconds())}.` +
        `${padNumber(date.getMilliseconds(), 3)}`
    );
}

function formatMessage(arguments_: unknown[]): string {
    return formatWithOptions({ colors: false, depth: 6 }, ...arguments_);
}

/** Append one line to ``DATA_DIR/logs/latest.log`` when the symlink/file exists. */
export function appendServerLogLine(
    level: string,
    functionName: string,
    message: string,
): void {
    const minRank = configuredLevelRank();
    const rank = LEVEL_RANK[level.toUpperCase()] ?? LEVEL_RANK.INFO;
    if (rank < minRank) {
        return;
    }

    const latestPath = getLatestLogPath();
    if (!latestPath || !existsSync(latestPath)) {
        return;
    }

    const line =
        `${formatTimestamp(new Date())} | ${LOGGER_NAME} | ` +
        `${functionName.padEnd(25)} | ${level.toUpperCase().padEnd(8)} | ${message}\n`;

    try {
        appendFileSync(latestPath, line, { encoding: "utf8" });
    } catch {
        // Avoid recursive console logging if the file disappears mid-write.
    }
}

/**
 * Tee ``console.*`` to ``DATA_DIR/logs/latest.log`` (follows the back-end symlink).
 * Safe to call once from Next.js ``instrumentation`` ``register``.
 */
export function setupServerFileLogging(): void {
    if (configured) {
        return;
    }
    configured = true;

    if (!process.env.DATA_DIR?.trim()) {
        return;
    }

    const methods = Object.keys(METHOD_LEVEL) as ConsoleMethod[];
    for (const method of methods) {
        const original = console[method].bind(console);
        const level = METHOD_LEVEL[method];
        console[method] = (...arguments_: unknown[]) => {
            original(...arguments_);
            appendServerLogLine(
                level,
                `console.${method}`,
                formatMessage(arguments_),
            );
        };
    }

    console.info(
        `Front-end server logging teed to ${getLatestLogPath() ?? "DATA_DIR/logs/latest.log"}`,
    );
}
