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

function passesNameQuery(
    name: string | undefined,
    query: string,
    includeMissing: boolean,
): boolean {
    const trimmed = query.trim();
    if (trimmed.length === 0) {
        return true;
    }
    if (!name) {
        return includeMissing;
    }
    return name.toLowerCase().includes(trimmed.toLowerCase());
}

function passesSelection(
    value: string | null | undefined,
    selected: string[],
    includeMissing: boolean,
): boolean {
    if (selected.length === 0) {
        return true;
    }
    if (!value) {
        return includeMissing;
    }
    return selected.includes(value);
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

function passesOpenWeightsOnly(
    isOpenWeights: boolean | null | undefined,
    openWeightsOnly: boolean,
    includeMissing: boolean,
): boolean {
    if (!openWeightsOnly) {
        return true;
    }
    if (typeof isOpenWeights !== "boolean") {
        return includeMissing;
    }
    return isOpenWeights === true;
}

export function filterModels(
    models: CombinedModel[],
    filters: ModelFiltersState,
): CombinedModel[] {
    return models.filter((model) => {
        if (
            !passesOpenWeightsOnly(
                model.is_open_weights,
                filters.openWeightsOnly,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesNameQuery(
                model.name,
                filters.nameQuery,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesSelection(
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
                model.pricing_input,
                filters.pricingInput,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.pricing_output,
                filters.pricingOutput,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesSelection(
                model.selected_provider,
                filters.providers,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.throughput,
                filters.throughput,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesRange(
                model.latency_ms,
                filters.latencyMs,
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
            !passesRange(
                model.parameters_b,
                filters.parametersB,
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
