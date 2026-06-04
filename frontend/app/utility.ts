export function formatTimestamp(value: number | undefined) {
    if (!value) {
        return value;
    }
    // Python uses seconds; JavaScript uses milliseconds
    return new Date(value * 1000).toLocaleDateString();
}

export function formatPrice(value: number | undefined) {
    if (!value) {
        return value;
    }
    return `$${value.toFixed(2)}`;
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
