import { CombinedModel } from "@/app/client";
import { filterModels } from "@/app/filters/apply-filters";
import { getFilterBounds } from "@/app/filters/filter-bounds";
import {
    createInitialUserChoices,
    FilterBounds,
    ModelFiltersState,
    NumberRange,
    resolveFilters,
    UserFilterChoices,
} from "@/app/filters/filter-types";
import {
    Dispatch,
    SetStateAction,
    useCallback,
    useMemo,
    useState,
} from "react";

function sameRange(
    left: NumberRange | undefined,
    right: NumberRange | undefined,
): boolean {
    return (
        left !== undefined &&
        right !== undefined &&
        left[0] === right[0] &&
        left[1] === right[1]
    );
}

function choiceRange(
    choice: NumberRange | undefined,
    bounds: NumberRange | undefined,
): NumberRange | undefined {
    // A span that still covers the whole dataset is not a user choice.
    // Keeping it would freeze stale bounds into a shared URL.
    return sameRange(choice, bounds) ? undefined : choice;
}

function toUserChoices(
    filters: ModelFiltersState,
    bounds: FilterBounds,
): UserFilterChoices {
    return {
        includeMissing: filters.includeMissing,
        openWeightsOnly: filters.openWeightsOnly,
        nameQuery: filters.nameQuery,
        creators: filters.creators,
        intelligenceIndex: choiceRange(
            filters.intelligenceIndex,
            bounds.intelligenceIndex,
        ),
        codingIndex: choiceRange(filters.codingIndex, bounds.codingIndex),
        agenticIndex: choiceRange(filters.agenticIndex, bounds.agenticIndex),
        pricingInput: choiceRange(filters.pricingInput, bounds.pricingInput),
        pricingOutput: choiceRange(
            filters.pricingOutput,
            bounds.pricingOutput,
        ),
        throughput: choiceRange(filters.throughput, bounds.throughput),
        latencyMs: choiceRange(filters.latencyMs, bounds.latencyMs),
        creationDate: choiceRange(filters.creationDate, bounds.creationDate),
        knowledgeCutoff: choiceRange(
            filters.knowledgeCutoff,
            bounds.knowledgeCutoff,
        ),
        contextLength: choiceRange(
            filters.contextLength,
            bounds.contextLength,
        ),
        parametersB: choiceRange(filters.parametersB, bounds.parametersB),
        usageCost: choiceRange(filters.usageCost, bounds.usageCost),
        inputModalities: filters.inputModalities,
        outputModalities: filters.outputModalities,
    };
}

export function useModelFilters(
    models: CombinedModel[],
    tokenMillions: number | undefined,
    initialChoices?: UserFilterChoices,
) {
    const bounds = useMemo(
        () => getFilterBounds(models, tokenMillions),
        [models, tokenMillions],
    );
    const [userChoices, setUserChoices] = useState<UserFilterChoices>(
        initialChoices ?? createInitialUserChoices,
    );

    const filters = useMemo(
        () => resolveFilters(userChoices, bounds),
        [userChoices, bounds],
    );

    const setFilters: Dispatch<SetStateAction<ModelFiltersState>> = useCallback(
        (action) => {
            setUserChoices((previousChoices) => {
                const previousFilters = resolveFilters(previousChoices, bounds);
                const nextFilters =
                    typeof action === "function"
                        ? action(previousFilters)
                        : action;
                return toUserChoices(nextFilters, bounds);
            });
        },
        [bounds],
    );

    const filteredModels = useMemo(
        () => filterModels(models, filters, tokenMillions),
        [models, filters, tokenMillions],
    );

    return { bounds, filters, setFilters, filteredModels, userChoices };
}
