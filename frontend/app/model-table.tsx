import { DataGrid } from "@mui/x-data-grid";
import { CombinedModel } from "./client";
import { MuiFontSans } from "@/app/mui-font";
import { columns } from "@/app/columns";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import ModelFilters from "@/app/filters/model-filters";
import { useModelFilters } from "@/app/filters/use-model-filters";

const noRowsOverlay = () => (
    <div className={"flex-center-everything"}>
        <p>No matching rows.</p>
    </div>
);

export default function ModelTable({ models }: { models: CombinedModel[] }) {
    const { bounds, filters, setFilters, filteredModels } =
        useModelFilters(models);

    return (
        <div style={{ width: "100%", height: "100%" }}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
                <div style={{ height: "50%", overflow: "auto" }}>
                    <ModelFilters
                        bounds={bounds}
                        filters={filters}
                        setFilters={setFilters}
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
