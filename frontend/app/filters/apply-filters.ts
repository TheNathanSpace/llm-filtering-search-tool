import { CombinedModel } from "@/app/client";
import { ModelFiltersState, NumberRange } from "@/app/filters/filter-types";

function passesRange(
    value: number | null | undefined,
    range: NumberRange | undefined,
    includeMissing: boolean,
): boolean {
    if (range === undefined) {
        return true;
    }
    if (typeof value !== "number") {
        return includeMissing;
    }
    return value >= range[0] && value <= range[1];
}

function passesCreators(
    creator: string | undefined,
    selected: string[],
    includeMissing: boolean,
): boolean {
    if (selected.length === 0) {
        return true;
    }
    if (!creator) {
        return includeMissing;
    }
    return selected.includes(creator);
}

export function filterModels(
    models: CombinedModel[],
    filters: ModelFiltersState,
): CombinedModel[] {
    return models.filter((model) => {
        if (
            !passesCreators(
                model.creator,
                filters.creators,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.created,
                filters.creationDate,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.knowledge_cutoff,
                filters.knowledgeCutoff,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.context_length,
                filters.contextLength,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        return true;
    });
}
