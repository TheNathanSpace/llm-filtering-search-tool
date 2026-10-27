export function formatTimestamp(value: number | undefined) {
    if (!value) {
        return value;
    }
    return new Date(value).toLocaleDateString();
}

export function formatPrice(value: number | undefined | null) {
    if (typeof value !== "number") {
        return "";
    }
    return `$${value.toFixed(2)}`;
}

function formatOneDecimal(value: number): string {
    const rounded = Math.round((value + Number.EPSILON) * 10) / 10;
    return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
}

export function formatThroughput(value: number | undefined | null) {
    if (typeof value !== "number") {
        return "";
    }
    return `${formatOneDecimal(value)} tok/s`;
}

/** Median time-to-first-token as seconds, always two decimal places (``3.11s``). */
export function formatLatencySeconds(value: number | undefined | null): string {
    if (typeof value !== "number") {
        return "";
    }
    return `${(value / 1000).toFixed(2)}s`;
}

/** Typed latency: seconds, optional trailing ``s``. Returns milliseconds. */
export function parseLatencySeconds(text: string): number | undefined {
    let normalized = text.trim().replaceAll(",", "");
    if (normalized.endsWith("s") || normalized.endsWith("S")) {
        normalized = normalized.slice(0, -1).trim();
    }
    if (normalized === "") {
        return undefined;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) {
        return undefined;
    }
    return parsed * 1000;
}

const CONTEXT_THOUSAND = 1000;
const CONTEXT_MILLION = 1_000_000;
/** Context lengths from this token count use millions; below it, thousands. */
const CONTEXT_MILLIONS_FROM = 500_000;

function trimTrailingZeros(fixed: string): string {
    return fixed.replace(/\.?0+$/, "");
}

/**
 * Context window: thousands under 500,000 tokens (``400k``), millions from
 * 500,000 (``1.2M``). At most two decimal places; trailing zeros are dropped.
 */
export function formatContextLength(value: number | undefined | null): string {
    if (typeof value !== "number") {
        return "";
    }
    if (value >= CONTEXT_MILLIONS_FROM) {
        return `${trimTrailingZeros((value / CONTEXT_MILLION).toFixed(2))}M`;
    }
    return `${trimTrailingZeros((value / CONTEXT_THOUSAND).toFixed(2))}k`;
}

/**
 * Typed context length. ``k``/``K`` is thousands, ``m``/``M`` is millions.
 * A bare number is the token count.
 */
export function parseContextLength(text: string): number | undefined {
    let normalized = text.trim().replaceAll(",", "");
    if (normalized === "") {
        return undefined;
    }
    const suffix = normalized.at(-1);
    let multiplier = 1;
    if (suffix === "k" || suffix === "K") {
        multiplier = CONTEXT_THOUSAND;
        normalized = normalized.slice(0, -1).trim();
    } else if (suffix === "m" || suffix === "M") {
        multiplier = CONTEXT_MILLION;
        normalized = normalized.slice(0, -1).trim();
    }
    if (normalized === "") {
        return undefined;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) {
        return undefined;
    }
    return parsed * multiplier;
}

export function formatNumber(value: number | undefined) {
    if (!value) {
        return value;
    }
    const number_ = Math.round((value + Number.EPSILON) * 100) / 100;
    return number_.toLocaleString();
}

/** Format parameter count in billions as e.g. ``7B`` / ``1.8B``. */
export function formatParametersB(value: number | undefined | null) {
    if (typeof value !== "number") {
        return "";
    }
    const rounded = Math.round((value + Number.EPSILON) * 100) / 100;
    const text =
        Number.isInteger(rounded) ||
        Math.abs(rounded - Math.round(rounded)) < 1e-9
            ? String(Math.round(rounded))
            : String(rounded);
    return `${text}B`;
}

export function formatCommaSeparatedList(
    value: readonly string[] | undefined | null,
): string {
    if (!value || value.length === 0) {
        return "";
    }
    return value.join(", ");
}

/**
 * Display form of an OpenRouter author slug.
 *
 * The stored creator is the lowercase id prefix (`openai`). Catalog names
 * usually start with the capitalized author (`OpenAI: Claude …`); that prefix
 * is the label. If the name has no `Author:` prefix but begins with a word
 * that starts the slug (`Reka` / `rekaai`), that word is kept. Otherwise the
 * slug is title-cased (`microsoft` → `Microsoft`).
 */
export function creatorLabel(
    slug: string | null | undefined,
    modelName: string | null | undefined,
): string {
    if (!slug) {
        return "";
    }
    const prefix = catalogAuthorPrefix(modelName);
    if (prefix) {
        return prefix;
    }
    const leadingWord = modelName?.split(/\s+/, 1)[0];
    if (leadingWord && slugStartsWithWord(slug, leadingWord)) {
        return leadingWord;
    }
    return humanizeSlug(slug);
}

function catalogAuthorPrefix(
    modelName: string | null | undefined,
): string | undefined {
    if (!modelName) {
        return undefined;
    }
    const separator = modelName.indexOf(": ");
    if (separator <= 0) {
        return undefined;
    }
    return modelName.slice(0, separator);
}

function slugStartsWithWord(slug: string, word: string): boolean {
    const token = word.toLowerCase().replaceAll(/[^a-z0-9]/g, "");
    const compact = slug.toLowerCase().replaceAll(/[^a-z0-9]/g, "");
    return token.length > 0 && compact.startsWith(token);
}

function humanizeSlug(slug: string): string {
    return slug
        .split(/[-_]+/)
        .filter((part) => part.length > 0)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

export function toTitleCase(label: string) {
    // https://stackoverflow.com/a/6475125/7492795
    let index, index_, string_;
    string_ = label.replaceAll(/([^\W_]+[^\s-]*) */g, function (txt) {
        return txt.charAt(0).toUpperCase() + txt.slice(1).toLowerCase();
    });

    // Certain minor words should be left lowercase unless
    // they are the first or last words in the string
    const lowers = [
        "A",
        "An",
        "The",
        "And",
        "But",
        "Or",
        "For",
        "Nor",
        "As",
        "At",
        "By",
        "For",
        "From",
        "In",
        "Into",
        "Near",
        "Of",
        "On",
        "Onto",
        "To",
        "With",
    ];
    for (index = 0, index_ = lowers.length; index < index_; index++)
        string_ = string_.replaceAll(
            new RegExp(String.raw`\s` + lowers[index] + String.raw`\s`, "g"),
            function (txt) {
                return txt.toLowerCase();
            },
        );

    // Certain words such as initialisms or acronyms should be left uppercase
    const uppers = ["Id", "Tv"];
    for (index = 0, index_ = uppers.length; index < index_; index++)
        string_ = string_.replaceAll(
            new RegExp(String.raw`\b` + uppers[index] + String.raw`\b`, "g"),
            uppers[index].toUpperCase(),
        );

    return string_;
}
