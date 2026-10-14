/** Lowercase and remove non-alphanumeric characters (spaces kept for tokenizing). */
export function stripPunctuation(text: string): string {
    return text.toLowerCase().replaceAll(/[^a-z0-9\s]+/g, "");
}

function queryWords(text: string): string[] {
    return stripPunctuation(text).split(/\s+/).filter(Boolean);
}

function fieldMatchesWords(
    field: string | undefined,
    words: string[],
): boolean {
    if (!field || words.length === 0) {
        return false;
    }
    const normalized = stripPunctuation(field);
    return words.every((word) => normalized.includes(word));
}

/** True when every query word appears in the name or the slug/id. */
export function modelMatchesWords(
    name: string | undefined,
    slug: string | undefined,
    words: string[],
): boolean {
    return (
        fieldMatchesWords(name, words) || fieldMatchesWords(slug, words)
    );
}

/**
 * Name/slug search:
 * - Matches readable names and OpenRouter ids/slugs
 * - Punctuation is ignored in the query and in those fields
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
