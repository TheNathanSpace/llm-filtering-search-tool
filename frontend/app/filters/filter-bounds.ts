import { CombinedModel } from "@/app/client";
import { FilterBounds, NumberRange } from "@/app/filters/filter-types";

export function getMinMax(
    values: (number | null | undefined)[],
): [number | undefined, number | undefined] {
    const filtered = values.filter((v): v is number => typeof v === "number");
    if (filtered.length === 0) {
        return [undefined, undefined];
    }
    // Preserve legitimate zeros (e.g. free-tier pricing); do not treat 0 as missing.
    return [Math.min(...filtered), Math.max(...filtered)];
}

export function getUniqueCreators(models: CombinedModel[]): string[] {
    const creators = new Set<string>();
    for (const model of models) {
        if (model.creator) {
            creators.add(model.creator);
        }
    }
    return [...creators].toSorted((a, b) => a.localeCompare(b));
}

function toRange(
    min: number | undefined,
    max: number | undefined,
): NumberRange | undefined {
    if (min === undefined || max === undefined) {
        return undefined;
    }
    return [min, max];
}

export function getFilterBounds(models: CombinedModel[]): FilterBounds {
    const [minCreationDate, maxCreationDate] = getMinMax(
        models.map((model) => model.created),
    );
    const [minKnowledgeCutoff, maxKnowledgeCutoff] = getMinMax(
        models.map((model) => model.knowledge_cutoff),
    );
    const [minContextLength, maxContextLength] = getMinMax(
        models.map((model) => model.context_length),
    );
    const [minIntelligence, maxIntelligence] = getMinMax(
        models.map((model) => model.benchmark_or_intelligence_index),
    );
    const [minCoding, maxCoding] = getMinMax(
        models.map((model) => model.benchmark_or_coding_index),
    );
    const [minAgentic, maxAgentic] = getMinMax(
        models.map((model) => model.benchmark_or_agentic_index),
    );
    const [minParametersB, maxParametersB] = getMinMax(
        models.map((model) => model.parameters_b),
    );
    const [minPricingInput, maxPricingInput] = getMinMax(
        models.map((model) => model.pricing_input),
    );
    const [minPricingOutput, maxPricingOutput] = getMinMax(
        models.map((model) => model.pricing_output),
    );

    return {
        creators: getUniqueCreators(models),
        intelligenceIndex: toRange(minIntelligence, maxIntelligence),
        codingIndex: toRange(minCoding, maxCoding),
        agenticIndex: toRange(minAgentic, maxAgentic),
        pricingInput: toRange(minPricingInput, maxPricingInput),
        pricingOutput: toRange(minPricingOutput, maxPricingOutput),
        creationDate: toRange(minCreationDate, maxCreationDate),
        knowledgeCutoff: toRange(minKnowledgeCutoff, maxKnowledgeCutoff),
        contextLength: toRange(minContextLength, maxContextLength),
        parametersB: toRange(minParametersB, maxParametersB),
    };
}
