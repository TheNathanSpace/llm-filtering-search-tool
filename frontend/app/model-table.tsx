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

const noRowsOverlay = () => (
    <div className={"flex-center-everything"}>
        <p>No matching rows.</p>
    </div>
);

export default function ModelTable({ models }: { models: CombinedModel[] }) {
    const { bounds, filters, setFilters, filteredModels } =
        useModelFilters(models);
    const [tokenMillionsText, setTokenMillionsText] = useState("");
    const tokenMillions = parseTokenMillions(tokenMillionsText);
    const columns = useMemo(
        () => columnsForTokenMillions(tokenMillions),
        [tokenMillions],
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
