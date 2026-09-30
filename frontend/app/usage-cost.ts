/**
 * Listed-price blend used to rank providers in `provider_choice.py`.
 * Cache reads are billed as ordinary input (90% input, 10% output).
 */
export const INPUT_WEIGHT = 0.9;
export const OUTPUT_WEIGHT = 0.1;

/** Positive token count in millions, or undefined when the box is empty or not usable. */
export function parseTokenMillions(text: string): number | undefined {
    const normalized = text.trim().replaceAll(",", "");
    if (normalized === "") {
        return undefined;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed) || parsed <= 0) {
        return undefined;
    }
    return parsed;
}

export function formatTokenMillions(value: number): string {
    const rounded = Math.round((value + Number.EPSILON) * 1000) / 1000;
    return String(rounded);
}

/**
 * Dollar cost of `tokenMillions` million tokens at listed $/1M rates.
 * Missing either rate leaves the cell empty.
 */
export function usageCost(
    tokenMillions: number,
    pricingInput: number | null | undefined,
    pricingOutput: number | null | undefined,
): number | undefined {
    if (typeof pricingInput !== "number" || typeof pricingOutput !== "number") {
        return undefined;
    }
    const perMillion =
        INPUT_WEIGHT * pricingInput + OUTPUT_WEIGHT * pricingOutput;
    return tokenMillions * perMillion;
}
