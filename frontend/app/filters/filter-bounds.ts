import { CombinedModel } from "@/app/client";
import { FilterBounds, NumberRange } from "@/app/filters/filter-types";

export function getMinMax(
    values: (number | null | undefined)[],
): [number | undefined, number | undefined] {
    const filtered = values.filter((v): v is number => typeof v === "number");
    if (filtered.length === 0) {
        return [undefined, undefined];
    }
    let min = Math.min(...filtered);
    let max = Math.max(...filtered);
    if (!min) {
        min = max;
    } else if (!max) {
        max = min;
    }
    return [min, max];
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

    return {
        creators: getUniqueCreators(models),
        creationDate: toRange(minCreationDate, maxCreationDate),
        knowledgeCutoff: toRange(minKnowledgeCutoff, maxKnowledgeCutoff),
        contextLength: toRange(minContextLength, maxContextLength),
    };
}
