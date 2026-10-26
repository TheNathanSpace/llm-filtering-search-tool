import {
    INPUT_MODALITY_OPTIONS,
    OUTPUT_MODALITY_OPTIONS,
} from "@/app/filters/modality-options";
import {
    createInitialUserChoices,
    NumberRange,
    UserFilterChoices,
} from "@/app/filters/filter-types";

/** Query record from the App Router `searchParams` prop. */
export type PageSearchQuery = Record<string, string | string[] | undefined>;

export type TableSortDirection = "asc" | "desc";

export type TableSortItem = {
    field: string;
    sort: TableSortDirection;
};

export type TableQueryState = {
    choices: UserFilterChoices;
    tokenMillionsText: string;
    sortModel: TableSortItem[];
    pinnedIds: string[];
};

/** Intelligence descending — omitted from the URL when it is the only sort. */
export const DEFAULT_TABLE_SORT: readonly TableSortItem[] = [
    { field: "benchmark_or_intelligence_index", sort: "desc" },
];

const SORT_ALIAS_TO_FIELD: Record<string, string> = {
    name: "name",
    openWeights: "is_open_weights",
    size: "parameters_b",
    intelligence: "benchmark_or_intelligence_index",
    coding: "benchmark_or_coding_index",
    agentic: "benchmark_or_agentic_index",
    context: "context_length",
    cost: "usage_cost",
    inputCost: "pricing_input",
    outputCost: "pricing_output",
    throughput: "throughput",
    latency: "latency_ms",
    created: "created",
    cutoff: "knowledge_cutoff",
    creator: "creator",
};

const FIELD_TO_SORT_ALIAS: Record<string, string> = Object.fromEntries(
    Object.entries(SORT_ALIAS_TO_FIELD).map(([alias, field]) => [field, alias]),
);

const KNOWN_SORT_FIELDS = new Set(Object.values(SORT_ALIAS_TO_FIELD));

type RangeChoiceField = {
    [Key in keyof UserFilterChoices]: UserFilterChoices[Key] extends
        | NumberRange
        | undefined
        ? Key
        : never;
}[keyof UserFilterChoices];

const RANGE_QUERY_FIELDS: readonly (readonly [string, RangeChoiceField])[] = [
    ["size", "parametersB"],
    ["intelligence", "intelligenceIndex"],
    ["coding", "codingIndex"],
    ["agentic", "agenticIndex"],
    ["context", "contextLength"],
    ["cost", "usageCost"],
    ["inputCost", "pricingInput"],
    ["outputCost", "pricingOutput"],
    ["throughput", "throughput"],
    ["latency", "latencyMs"],
    ["created", "creationDate"],
    ["cutoff", "knowledgeCutoff"],
];

function readList(query: PageSearchQuery, key: string): string[] {
    const value = query[key];
    if (typeof value === "string") {
        return value === "" ? [] : [value];
    }
    if (Array.isArray(value)) {
        return value.filter((item) => item !== "");
    }
    return [];
}

function readFirst(query: PageSearchQuery, key: string): string | undefined {
    return readList(query, key)[0];
}

function uniqueInOrder(values: readonly string[]): string[] {
    const seen = new Set<string>();
    const unique: string[] = [];
    for (const value of values) {
        const trimmed = value.trim();
        if (trimmed === "" || seen.has(trimmed)) {
            continue;
        }
        seen.add(trimmed);
        unique.push(trimmed);
    }
    return unique;
}

function formatQueryNumber(value: number): string {
    const rounded = Math.round((value + Number.EPSILON) * 1e6) / 1e6;
    return String(rounded);
}

function parseRange(text: string | undefined): NumberRange | undefined {
    if (text === undefined) {
        return undefined;
    }
    const parts = text.split(",");
    if (parts.length !== 2) {
        return undefined;
    }
    const start = Number(parts[0]);
    const end = Number(parts[1]);
    if (!Number.isFinite(start) || !Number.isFinite(end)) {
        return undefined;
    }
    if (start <= end) {
        return [start, end];
    }
    return [end, start];
}

function formatRange(range: NumberRange | undefined): string | undefined {
    if (range === undefined) {
        return undefined;
    }
    return `${formatQueryNumber(range[0])},${formatQueryNumber(range[1])}`;
}

function parseModalities<T extends string>(
    values: readonly string[],
    allowed: readonly T[],
): T[] {
    const selected = new Set(values);
    return allowed.filter((item) => selected.has(item));
}

function parseSort(value: string | undefined): TableSortItem[] {
    if (value === undefined) {
        return [...DEFAULT_TABLE_SORT];
    }
    if (value === "none") {
        return [];
    }
    const items: TableSortItem[] = [];
    for (const part of value.split(",")) {
        const separator = part.lastIndexOf(":");
        if (separator <= 0) {
            continue;
        }
        const name = part.slice(0, separator);
        const direction = part.slice(separator + 1);
        if (direction !== "asc" && direction !== "desc") {
            continue;
        }
        const aliased = SORT_ALIAS_TO_FIELD[name];
        const field =
            aliased ?? (KNOWN_SORT_FIELDS.has(name) ? name : undefined);
        if (field === undefined) {
            continue;
        }
        items.push({ field, sort: direction });
    }
    if (items.length === 0) {
        return [...DEFAULT_TABLE_SORT];
    }
    return items;
}

function serializeSort(
    sortModel: readonly TableSortItem[],
): string | undefined {
    if (sortModel.length === 0) {
        return "none";
    }
    const [only] = sortModel;
    const [defaultSort] = DEFAULT_TABLE_SORT;
    if (
        sortModel.length === 1 &&
        only !== undefined &&
        only.field === defaultSort.field &&
        only.sort === defaultSort.sort
    ) {
        return undefined;
    }
    return sortModel
        .map((item) => {
            const alias = FIELD_TO_SORT_ALIAS[item.field] ?? item.field;
            return `${alias}:${item.sort}`;
        })
        .join(",");
}

/**
 * Drop a usage-cost sort when that column is hidden (no positive token count).
 * An empty remainder falls back to the default intelligence sort.
 */
export function sortModelForTokenCount(
    sortModel: readonly TableSortItem[],
    tokenMillions: number | undefined,
): TableSortItem[] {
    if (tokenMillions !== undefined) {
        return sortModel as TableSortItem[];
    }
    const visible = sortModel.filter((item) => item.field !== "usage_cost");
    if (visible.length === sortModel.length) {
        return sortModel as TableSortItem[];
    }
    if (visible.length === 0) {
        return [...DEFAULT_TABLE_SORT];
    }
    return visible;
}

export function parseTableQuery(query: PageSearchQuery): TableQueryState {
    const choices = createInitialUserChoices();
    if (readFirst(query, "missing") === "0") {
        choices.includeMissing = false;
    }
    if (readFirst(query, "openWeights") === "1") {
        choices.openWeightsOnly = true;
    }
    if (readFirst(query, "pinnedOnly") === "1") {
        choices.pinnedOnly = true;
    }
    choices.nameQuery = readFirst(query, "name") ?? "";
    choices.creators = uniqueInOrder(readList(query, "creator"));
    for (const [parameter, field] of RANGE_QUERY_FIELDS) {
        const range = parseRange(readFirst(query, parameter));
        if (range !== undefined) {
            choices[field] = range;
        }
    }
    choices.inputModalities = parseModalities(
        readList(query, "input"),
        INPUT_MODALITY_OPTIONS,
    );
    choices.outputModalities = parseModalities(
        readList(query, "output"),
        OUTPUT_MODALITY_OPTIONS,
    );
    return {
        choices,
        tokenMillionsText: readFirst(query, "tokens") ?? "",
        sortModel: parseSort(readFirst(query, "sort")),
        pinnedIds: uniqueInOrder(readList(query, "pin")),
    };
}

export function serializeTableQuery(state: TableQueryState): string {
    const parameters = new URLSearchParams();
    const { choices } = state;
    if (!choices.includeMissing) {
        parameters.set("missing", "0");
    }
    if (choices.openWeightsOnly) {
        parameters.set("openWeights", "1");
    }
    if (choices.pinnedOnly) {
        parameters.set("pinnedOnly", "1");
    }
    if (choices.nameQuery !== "") {
        parameters.set("name", choices.nameQuery);
    }
    for (const creator of uniqueInOrder(choices.creators)) {
        parameters.append("creator", creator);
    }
    for (const [parameter, field] of RANGE_QUERY_FIELDS) {
        const formatted = formatRange(choices[field]);
        if (formatted !== undefined) {
            parameters.set(parameter, formatted);
        }
    }
    if (state.tokenMillionsText !== "") {
        parameters.set("tokens", state.tokenMillionsText);
    }
    for (const modality of choices.inputModalities) {
        if ((INPUT_MODALITY_OPTIONS as readonly string[]).includes(modality)) {
            parameters.append("input", modality);
        }
    }
    for (const modality of choices.outputModalities) {
        if ((OUTPUT_MODALITY_OPTIONS as readonly string[]).includes(modality)) {
            parameters.append("output", modality);
        }
    }
    const sort = serializeSort(state.sortModel);
    if (sort !== undefined) {
        parameters.set("sort", sort);
    }
    for (const id of uniqueInOrder(state.pinnedIds)) {
        parameters.append("pin", id);
    }
    return parameters.toString();
}
