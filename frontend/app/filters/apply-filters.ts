import { CombinedModel } from "@/app/client";
import {
    FilterBounds,
    ModelFiltersState,
    NumberRange,
} from "@/app/filters/filter-types";
import { passesNameQuery } from "@/app/filters/name-query";
import { usageCost } from "@/app/usage-cost";
import { creatorLabel } from "@/app/utility";

/** A span that still covers every present value is not an active filter. */
function constrainingRange(
    range: NumberRange | undefined,
    bounds: NumberRange | undefined,
): NumberRange | undefined {
    if (range === undefined) {
        return undefined;
    }
    if (
        bounds !== undefined &&
        range[0] === bounds[0] &&
        range[1] === bounds[1]
    ) {
        return undefined;
    }
    return range;
}

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
    tokenMillions: number | undefined,
    pinnedIds: ReadonlySet<string>,
    bounds: FilterBounds,
): CombinedModel[] {
    const includeMissing = filters.includeMissing;

    function passesBoundedRange(
        value: number | null | undefined,
        range: NumberRange | undefined,
        fieldBounds: NumberRange | undefined,
    ): boolean {
        return passesRange(
            value,
            constrainingRange(range, fieldBounds),
            includeMissing,
        );
    }

    return models.filter((model) => {
        if (filters.pinnedOnly && !pinnedIds.has(model.id)) {
            return false;
        }
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
                model.id,
                filters.nameQuery,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesSelection(
                creatorLabel(model.creator, model.name),
                filters.creators,
                filters.includeMissing,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.benchmark_or_intelligence_index,
                filters.intelligenceIndex,
                bounds.intelligenceIndex,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.benchmark_coding,
                filters.codingIndex,
                bounds.codingIndex,
            )
        ) {
            return false;
        }
        const cost =
            tokenMillions === undefined
                ? undefined
                : usageCost(
                      tokenMillions,
                      model.pricing_input,
                      model.pricing_output,
                  );
        if (!passesBoundedRange(cost, filters.usageCost, bounds.usageCost)) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.pricing_input,
                filters.pricingInput,
                bounds.pricingInput,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.pricing_output,
                filters.pricingOutput,
                bounds.pricingOutput,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.throughput,
                filters.throughput,
                bounds.throughput,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.latency_ms,
                filters.latencyMs,
                bounds.latencyMs,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.created,
                filters.creationDate,
                bounds.creationDate,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.knowledge_cutoff,
                filters.knowledgeCutoff,
                bounds.knowledgeCutoff,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.context_length,
                filters.contextLength,
                bounds.contextLength,
            )
        ) {
            return false;
        }
        if (
            !passesBoundedRange(
                model.parameters_b,
                filters.parametersB,
                bounds.parametersB,
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
