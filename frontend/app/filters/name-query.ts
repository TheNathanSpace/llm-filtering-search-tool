const NUMBER_SPAN = /\d+(?:\.\d+)*/g;

/** Lowercase. Keep a decimal point between digits. Other punctuation becomes a space. */
export function normalizeSearchText(text: string): string {
    const lower = text.toLowerCase();
    let normalized = "";
    for (let index = 0; index < lower.length; index += 1) {
        const character = lower[index] ?? "";
        if (/[a-z0-9\s]/.test(character)) {
            normalized += character;
            continue;
        }
        const previous = lower[index - 1] ?? "";
        const next = lower[index + 1] ?? "";
        if (character === "." && /\d/.test(previous) && /\d/.test(next)) {
            normalized += ".";
            continue;
        }
        normalized += " ";
    }
    return normalized;
}

function queryWords(text: string): string[] {
    return normalizeSearchText(text).split(/\s+/).filter(Boolean);
}

function isNumberToken(word: string): boolean {
    return /^\d+(?:\.\d+)*$/.test(word);
}

function numericSpans(normalized: string): Set<string> {
    const matched = normalized.match(NUMBER_SPAN);
    if (!matched) {
        return new Set();
    }
    return new Set(matched);
}

function fieldMatchesWords(
    field: string | undefined,
    words: string[],
): boolean {
    if (!field || words.length === 0) {
        return false;
    }
    const normalized = normalizeSearchText(field);
    const spans = numericSpans(normalized);
    return words.every((word) => {
        if (isNumberToken(word)) {
            return spans.has(word);
        }
        return normalized.includes(word);
    });
}

/** True when every query word appears in the name or the slug/id. */
export function modelMatchesWords(
    name: string | undefined,
    slug: string | undefined,
    words: string[],
): boolean {
    return fieldMatchesWords(name, words) || fieldMatchesWords(slug, words);
}

/**
 * Name/slug search:
 * - Matches readable names and OpenRouter ids/slugs
 * - Punctuation is ignored, except a decimal point between digits
 * - A number matches that whole numeric span, including inside a word (`4.1` matches `v4.1`)
 * - Commas separate OR'd alternatives
 * - A leading `-` on a comma unit excludes models that match every word in it
 */
export function passesNameQuery(
    name: string | undefined,
    slug: string | undefined,
    query: string,
    includeMissing: boolean,
): boolean {
    const trimmed = query.trim();
    if (trimmed.length === 0) {
        return true;
    }

    const units = trimmed
        .split(",")
        .map((unit) => unit.trim())
        .filter((unit) => unit.length > 0);

    const includes: string[][] = [];
    const excludes: string[][] = [];

    for (const unit of units) {
        if (unit.startsWith("-")) {
            const words = queryWords(unit.slice(1));
            if (words.length > 0) {
                excludes.push(words);
            }
            continue;
        }
        const words = queryWords(unit);
        if (words.length > 0) {
            includes.push(words);
        }
    }

    if (includes.length === 0 && excludes.length === 0) {
        return true;
    }

    if (!name && !slug) {
        return includeMissing;
    }

    if (
        includes.length > 0 &&
        !includes.some((words) => modelMatchesWords(name, slug, words))
    ) {
        return false;
    }

    for (const words of excludes) {
        if (modelMatchesWords(name, slug, words)) {
            return false;
        }
    }

    return true;
}
