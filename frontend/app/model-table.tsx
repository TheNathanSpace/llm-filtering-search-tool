import { DataGrid, GridSortModel } from "@mui/x-data-grid";
import { CombinedModel } from "./client";
import { MuiFontSans } from "@/app/mui-font";
import { columnsForTokenMillions } from "@/app/columns";
import { parseTokenMillions } from "@/app/usage-cost";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import ModelFilters from "@/app/filters/model-filters";
import {
    PageSearchQuery,
    parseTableQuery,
    sortModelForTokenCount,
    TableSortItem,
} from "@/app/filters/filter-query";
import { useModelFilters } from "@/app/filters/use-model-filters";
import { useSyncTableQuery } from "@/app/filters/use-sync-table-query";
import { useCallback, useMemo, useState } from "react";

const POPULATING_MESSAGE =
    "The models database is still being populated. Check back in a little (or maybe a lot) while.";

function makeNoRowsOverlay(message: string) {
    return function NoRowsOverlay() {
        return (
            <div
                className={"flex-center-everything"}
                style={{ padding: "1.5rem" }}
            >
                <p style={{ textAlign: "center", maxWidth: "28rem" }}>
                    {message}
                </p>
            </div>
        );
    };
}

function toTableSort(model: GridSortModel): TableSortItem[] {
    return model.flatMap((item) => {
        if (item.sort === "asc" || item.sort === "desc") {
            return [{ field: item.field, sort: item.sort }];
        }
        return [];
    });
}

export default function ModelTable({
    models,
    populating = false,
    initialQuery,
}: {
    models: CombinedModel[];
    /** True while the first (or an in-flight) DB rebuild has nothing to show yet. */
    populating?: boolean;
    /** Query string from the first request, used to restore a shared setup. */
    initialQuery: PageSearchQuery;
}) {
    const [initialSetup] = useState(() => {
        const parsed = parseTableQuery(initialQuery);
        return {
            ...parsed,
            sortModel: sortModelForTokenCount(
                parsed.sortModel,
                parseTokenMillions(parsed.tokenMillionsText),
            ),
        };
    });
    const [tokenMillionsText, setTokenMillionsText] = useState(
        initialSetup.tokenMillionsText,
    );
    const [sortModel, setSortModel] = useState(initialSetup.sortModel);
    const [pinnedIds, setPinnedIds] = useState(initialSetup.pinnedIds);
    const tokenMillions = parseTokenMillions(tokenMillionsText);
    const pinnedIdSet = useMemo(() => new Set(pinnedIds), [pinnedIds]);
    const { bounds, filters, setFilters, filteredModels, userChoices } =
        useModelFilters(
            models,
            tokenMillions,
            initialSetup.choices,
            pinnedIdSet,
        );
    useSyncTableQuery({
        choices: userChoices,
        tokenMillionsText,
        sortModel,
        pinnedIds,
    });
    const togglePin = useCallback((id: string) => {
        setPinnedIds((previous) =>
            previous.includes(id)
                ? previous.filter((item) => item !== id)
                : [...previous, id],
        );
    }, []);
    const clearPins = useCallback(() => {
        setPinnedIds([]);
        setFilters((previous) => ({
            ...previous,
            pinnedOnly: false,
        }));
    }, [setFilters]);
    const columns = useMemo(
        () =>
            columnsForTokenMillions(tokenMillions, {
                pinnedIds: pinnedIdSet,
                onTogglePin: togglePin,
            }),
        [tokenMillions, pinnedIdSet, togglePin],
    );

    const emptyMessage = useMemo(() => {
        if (models.length === 0 && populating) {
            return POPULATING_MESSAGE;
        }
        if (models.length === 0) {
            return "No models loaded.";
        }
        return "No rows match your current filters.";
    }, [models.length, populating]);

    const noRowsOverlay = useMemo(
        () => makeNoRowsOverlay(emptyMessage),
        [emptyMessage],
    );

    return (
        <div style={{ width: "100%", height: "100%" }}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
                <div style={{ height: "50%", overflow: "auto" }}>
                    <ModelFilters
                        bounds={bounds}
                        filters={filters}
                        setFilters={setFilters}
                        tokenMillions={tokenMillionsText}
                        onTokenMillionsChange={(value) => {
                            setTokenMillionsText(value);
                            setSortModel((previous) =>
                                sortModelForTokenCount(
                                    previous,
                                    parseTokenMillions(value),
                                ),
                            );
                        }}
                        onClearPins={clearPins}
                    />
                </div>
                <MuiFontSans style={{ height: "50%", width: "100%" }}>
                    <DataGrid
                        rows={filteredModels}
                        columns={columns}
                        getRowId={(row) => row.id}
                        autoHeight={false}
                        disableVirtualization
                        sx={{
                            "& .MuiDataGrid-cell:focus, & .MuiDataGrid-cell:focus-within, & .MuiDataGrid-columnHeader:focus, & .MuiDataGrid-columnHeader:focus-within":
                                {
                                    outline: "none !important",
                                },
                        }}
                        sortModel={sortModel}
                        onSortModelChange={(model) => {
                            setSortModel(toTableSort(model));
                        }}
                        slots={{
                            noRowsOverlay: noRowsOverlay,
                            noResultsOverlay: noRowsOverlay,
                        }}
                    />
                </MuiFontSans>
            </LocalizationProvider>
        </div>
    );
}
