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

function passesModalities<T extends string>(
    actual: readonly T[] | undefined,
    required: readonly T[],
    includeMissing: boolean,
): boolean {
    if (required.length === 0) {
        return true;
    }
    if (!actual) {
        return includeMissing;
    }
    return required.every((item) => actual.includes(item));
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
                model.benchmark_or_intelligence_index,
                filters.intelligenceIndex,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.benchmark_or_coding_index,
                filters.codingIndex,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.benchmark_or_agentic_index,
                filters.agenticIndex,
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
        if (
            !passesModalities(
                model.input_modalities,
                filters.inputModalities,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesModalities(
                model.output_modalities,
                filters.outputModalities,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        return true;
    });
}
