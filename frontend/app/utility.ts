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
const PARAMETER_THOUSAND = 1000;
const PARAMETER_MILLION = 1_000_000;
const PARAMETER_BILLION = 1_000_000_000;
const PARAMETER_TRILLION = 1_000_000_000_000;
/** Stay on a unit through this many of it; the next count uses the next unit. */
const MAGNITUDE_SWITCH_AT = 900;

type MagnitudeUnit = {
    size: number;
    suffix: string;
};

const CONTEXT_UNITS: readonly MagnitudeUnit[] = [
    { size: CONTEXT_THOUSAND, suffix: "k" },
    { size: CONTEXT_MILLION, suffix: "M" },
];

const PARAMETER_UNITS: readonly MagnitudeUnit[] = [
    { size: PARAMETER_THOUSAND, suffix: "k" },
    { size: PARAMETER_MILLION, suffix: "M" },
    { size: PARAMETER_BILLION, suffix: "B" },
    { size: PARAMETER_TRILLION, suffix: "T" },
];

const PARAMETER_SUFFIX_SCALE: Readonly<Record<string, number>> = {
    k: PARAMETER_THOUSAND,
    m: PARAMETER_MILLION,
    b: PARAMETER_BILLION,
    t: PARAMETER_TRILLION,
};

/** Nearest whole unit below 100; nearest 10 from 100 through 900. */
function roundMagnitudeCoefficient(quotient: number): number {
    if (quotient >= 100 && quotient <= MAGNITUDE_SWITCH_AT) {
        return Math.round(quotient / 10) * 10;
    }
    return Math.round(quotient);
}

/**
 * Compact count. Stays on a unit through 900 of that unit, then steps up.
 * A coefficient from 100 through 900 displays with a zero ones digit (``130``).
 */
function formatMagnitude(
    count: number,
    units: readonly MagnitudeUnit[],
): string {
    let unit = units[0];
    for (let index = 0; index < units.length - 1; index += 1) {
        if (Math.abs(count) > units[index].size * MAGNITUDE_SWITCH_AT) {
            unit = units[index + 1];
        } else {
            break;
        }
    }
    return `${roundMagnitudeCoefficient(count / unit.size)}${unit.suffix}`;
}

/**
 * Context window: thousands through 900,000 tokens (``130k``), millions above
 * that (``1M``). A coefficient from 100 through 900 rounds to the nearest 10.
 */
export function formatContextLength(value: number | undefined | null): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "";
    }
    return formatMagnitude(value, CONTEXT_UNITS);
}

/** Full number with thousands separators (``1,234,567``). */
export function formatReadableNumber(value: number | undefined | null): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "";
    }
    return value.toLocaleString("en-US", { maximumFractionDigits: 20 });
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

/**
 * Parameter count stored in billions: thousands (``400k``), millions (``500M``),
 * billions (``410B``), trillions (``1T``). Same 100–900 rounding as context length.
 */
export function formatParametersB(value: number | undefined | null): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "";
    }
    return formatMagnitude(
        Math.round(value * PARAMETER_BILLION),
        PARAMETER_UNITS,
    );
}

/** Stored billions as a parameter count with thousands separators. */
export function formatParameterCount(value: number | undefined | null): string {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        return "";
    }
    return Math.round(value * PARAMETER_BILLION).toLocaleString("en-US");
}

/**
 * Typed size. ``k``/``m``/``b``/``t`` (any case) are parameter-count units.
 * A bare number is the parameter count. Returns billions.
 */
export function parseParameterCount(text: string): number | undefined {
    let normalized = text.trim().replaceAll(",", "");
    if (normalized === "") {
        return undefined;
    }
    const suffix = normalized.at(-1)?.toLowerCase();
    const parametersPerUnit =
        suffix === undefined ? undefined : PARAMETER_SUFFIX_SCALE[suffix];
    if (parametersPerUnit !== undefined) {
        normalized = normalized.slice(0, -1).trim();
    }
    if (normalized === "") {
        return undefined;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) {
        return undefined;
    }
    return (parsed * (parametersPerUnit ?? 1)) / PARAMETER_BILLION;
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
