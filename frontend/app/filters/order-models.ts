import { CombinedModel } from "@/app/client";
import { pinsLeadTable, TableSortItem } from "@/app/filters/filter-query";
import { usageCost } from "@/app/usage-cost";
import { creatorLabel } from "@/app/utility";

const collator = new Intl.Collator();

type SortValue = string | number | boolean | undefined;

function definedSortValue(value: unknown): SortValue {
    if (
        typeof value === "string" ||
        typeof value === "number" ||
        typeof value === "boolean"
    ) {
        return value;
    }
    return undefined;
}

function sortValue(
    model: CombinedModel,
    field: string,
    tokenMillions: number | undefined,
): SortValue {
    if (field === "creator") {
        return creatorLabel(model.creator, model.name);
    }
    if (field === "usage_cost") {
        if (tokenMillions === undefined) {
            return undefined;
        }
        return usageCost(
            tokenMillions,
            model.pricing_input,
            model.pricing_output,
        );
    }
    return definedSortValue(model[field as keyof CombinedModel]);
}

/** Same null and direction rules as the Data Grid column comparators. */
function compareSortValues(
    left: SortValue,
    right: SortValue,
    textual: boolean,
): number {
    if (left === undefined && right !== undefined) {
        return -1;
    }
    if (right === undefined && left !== undefined) {
        return 1;
    }
    if (left === undefined || right === undefined) {
        return 0;
    }
    if (textual) {
        return collator.compare(String(left), String(right));
    }
    return Number(left) - Number(right);
}

function sortModels(
    models: readonly CombinedModel[],
    sortModel: readonly TableSortItem[],
    tokenMillions: number | undefined,
): CombinedModel[] {
    return models.toSorted((left, right) => {
        for (const item of sortModel) {
            const textual = item.field === "name" || item.field === "creator";
            const comparison = compareSortValues(
                sortValue(left, item.field, tokenMillions),
                sortValue(right, item.field, tokenMillions),
                textual,
            );
            if (comparison !== 0) {
                return item.sort === "desc" ? -comparison : comparison;
            }
        }
        return 0;
    });
}

/** Filtered rows plus every pinned model, including ones the filters removed. */
function rowsForTable(
    models: readonly CombinedModel[],
    filteredModels: readonly CombinedModel[],
    pinnedIds: ReadonlySet<string>,
): CombinedModel[] {
    const included = new Set(filteredModels.map((model) => model.id));
    return models.filter(
        (model) => included.has(model.id) || pinnedIds.has(model.id),
    );
}

/**
 * Order rows for the table.
 * Pinned models stay in the list even when they fail the filters, and lead unless a non-default sort is active.
 */
export function orderFilteredModels(
    models: readonly CombinedModel[],
    filteredModels: readonly CombinedModel[],
    pinnedIds: ReadonlySet<string>,
    sortModel: readonly TableSortItem[],
    tokenMillions: number | undefined,
): CombinedModel[] {
    const visible = rowsForTable(models, filteredModels, pinnedIds);
    const sorted =
        sortModel.length === 0
            ? [...visible]
            : sortModels(visible, sortModel, tokenMillions);
    if (!pinsLeadTable(sortModel)) {
        return sorted;
    }
    const pinned: CombinedModel[] = [];
    const rest: CombinedModel[] = [];
    for (const model of sorted) {
        if (pinnedIds.has(model.id)) {
            pinned.push(model);
        } else {
            rest.push(model);
        }
    }
    return [...pinned, ...rest];
}
