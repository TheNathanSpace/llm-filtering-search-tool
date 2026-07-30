import { DataGrid } from "@mui/x-data-grid";
import { CombinedModel } from "./client";
import { MuiFontSans } from "@/app/mui-font";
import { columns } from "@/app/columns";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import ModelFilters from "@/app/filters/model-filters";
import { useModelFilters } from "@/app/filters/use-model-filters";

export default function ModelTable({ models }: { models: CombinedModel[] }) {
    const { bounds, filters, setFilters, filteredModels } =
        useModelFilters(models);

    return (
        <div style={{ width: "100%", height: "100%" }}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
                <div style={{ height: "50%" }}>
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
                        getRowId={(row) => row.name}
                        autoHeight={false}
                    />
                </MuiFontSans>
            </LocalizationProvider>
        </div>
    );
}
