import { CombinedModel } from "@/app/client";
import { filterModels } from "@/app/filters/apply-filters";
import { getFilterBounds } from "@/app/filters/filter-bounds";
import {
    createInitialUserChoices,
    ModelFiltersState,
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

function toUserChoices(filters: ModelFiltersState): UserFilterChoices {
    return {
        includeMissing: filters.includeMissing,
        creators: filters.creators,
        creationDate: filters.creationDate,
        knowledgeCutoff: filters.knowledgeCutoff,
        contextLength: filters.contextLength,
    };
}

export function useModelFilters(models: CombinedModel[]) {
    const bounds = useMemo(() => getFilterBounds(models), [models]);
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
                return toUserChoices(nextFilters);
            });
        },
        [bounds],
    );

    const filteredModels = useMemo(
        () => filterModels(models, filters),
        [models, filters],
    );

    return { bounds, filters, setFilters, filteredModels };
}
