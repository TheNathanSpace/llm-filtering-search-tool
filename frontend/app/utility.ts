export function formatTimestamp(value: number | undefined) {
    if (!value) {
        return value;
    }
    return new Date(value).toLocaleDateString();
}

export function formatPrice(value: number | undefined) {
    if (!value) {
        return value;
    }
    return `$${value.toFixed(2)}`;
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
        Number.isInteger(rounded) || Math.abs(rounded - Math.round(rounded)) < 1e-9
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
