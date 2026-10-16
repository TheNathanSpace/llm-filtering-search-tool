import { DataGrid } from "@mui/x-data-grid";
import { CombinedModel } from "./client";
import { MuiFontSans } from "@/app/mui-font";
import { columnsForTokenMillions } from "@/app/columns";
import { parseTokenMillions } from "@/app/usage-cost";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import ModelFilters from "@/app/filters/model-filters";
import { useModelFilters } from "@/app/filters/use-model-filters";
import { useMemo, useState } from "react";

const POPULATING_MESSAGE =
    "The models database is still being populated. Check back in a little (or maybe a lot) while.";

function makeNoRowsOverlay(message: string) {
    return function NoRowsOverlay() {
        return (
            <div className={"flex-center-everything"} style={{ padding: "1.5rem" }}>
                <p style={{ textAlign: "center", maxWidth: "28rem" }}>{message}</p>
            </div>
        );
    };
}

export default function ModelTable({
    models,
    populating = false,
}: {
    models: CombinedModel[];
    /** True while the first (or an in-flight) DB rebuild has nothing to show yet. */
    populating?: boolean;
}) {
    const [tokenMillionsText, setTokenMillionsText] = useState("");
    const tokenMillions = parseTokenMillions(tokenMillionsText);
    const { bounds, filters, setFilters, filteredModels } = useModelFilters(
        models,
        tokenMillions,
    );
    const columns = useMemo(
        () => columnsForTokenMillions(tokenMillions),
        [tokenMillions],
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
                        onTokenMillionsChange={setTokenMillionsText}
                    />
                </div>
                <MuiFontSans style={{ height: "50%", width: "100%" }}>
                    <DataGrid
                        rows={filteredModels}
                        columns={columns}
                        getRowId={(row) => row.id}
                        autoHeight={false}
                        disableVirtualization
                        initialState={{
                            sorting: {
                                sortModel: [
                                    {
                                        field: "benchmark_or_intelligence_index",
                                        sort: "desc",
                                    },
                                ],
                            },
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
