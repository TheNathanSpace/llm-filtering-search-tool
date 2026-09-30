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

function toUserChoices(
    filters: ModelFiltersState,
    bounds: FilterBounds,
): UserFilterChoices {
    // A span that still covers every calculated cost is not a user choice.
    // Keeping it would freeze stale dollar bounds after the token count changes.
    const usageCost = sameRange(filters.usageCost, bounds.usageCost)
        ? undefined
        : filters.usageCost;
    return {
        includeMissing: filters.includeMissing,
        openWeightsOnly: filters.openWeightsOnly,
        nameQuery: filters.nameQuery,
        creators: filters.creators,
        intelligenceIndex: filters.intelligenceIndex,
        codingIndex: filters.codingIndex,
        agenticIndex: filters.agenticIndex,
        pricingInput: filters.pricingInput,
        pricingOutput: filters.pricingOutput,
        providers: filters.providers,
        throughput: filters.throughput,
        latencyMs: filters.latencyMs,
        creationDate: filters.creationDate,
        knowledgeCutoff: filters.knowledgeCutoff,
        contextLength: filters.contextLength,
        parametersB: filters.parametersB,
        usageCost,
        inputModalities: filters.inputModalities,
        outputModalities: filters.outputModalities,
    };
}

export function useModelFilters(
    models: CombinedModel[],
    tokenMillions: number | undefined,
) {
    const bounds = useMemo(
        () => getFilterBounds(models, tokenMillions),
        [models, tokenMillions],
    );
    const [userChoices, setUserChoices] = useState<UserFilterChoices>(
        createInitialUserChoices,
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

    return { bounds, filters, setFilters, filteredModels };
}
