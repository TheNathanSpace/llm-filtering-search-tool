import { DataGrid } from "@mui/x-data-grid";
import { CombinedModel } from "./client";
import { MuiFontSans } from "@/app/mui-font";
import { Autocomplete, Chip, TextField } from "@mui/material";
import { columns } from "@/app/columns";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import FilterOption from "@/app/filter-option";
import DateRangeFilter from "@/app/date-range-filter";
import dayjs from "dayjs";

function getMinMax(
    values: (number | undefined)[],
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

export default function ModelTable({ models }: { models: CombinedModel[] }) {
    function getUniqueCreators(models: CombinedModel[]) {
        const creators = new Set<string>();
        for (const model of models) {
            if (model.creator) {
                creators.add(model.creator);
            }
        }
        return [...creators];
    }

    const [minCreationDate, maxCreationDate] = getMinMax(
        models.map((model) => model.created),
    );
    const [minKnowledgeCutoff, maxKnowledgeCutoff] = getMinMax(
        models.map((model) => model.knowledge_cutoff),
    );

    return (
        <div style={{ width: "100%" }}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
                <FilterOption name={"Creators"}>
                    <MuiFontSans style={{ width: "100%" }}>
                        <Autocomplete
                            multiple={true}
                            options={getUniqueCreators(models)}
                            disableCloseOnSelect={true}
                            renderInput={(parameters) => (
                                <TextField
                                    {...parameters}
                                    label="Pick creators"
                                />
                            )}
                            filterSelectedOptions={true}
                            fullWidth={true}
                            renderValue={(value, getTagProperties) =>
                                value.map((option, index) => {
                                    const { onDelete, ...other } =
                                        getTagProperties({
                                            index,
                                        });

                                    return (
                                        <Chip
                                            label={option}
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                if (onDelete) {
                                                    onDelete(event);
                                                }
                                            }}
                                            onDelete={onDelete}
                                            {...other}
                                            key={index}
                                        />
                                    );
                                })
                            }
                        />
                    </MuiFontSans>
                </FilterOption>
                {minCreationDate && maxCreationDate && (
                    <DateRangeFilter
                        name={"Creation date"}
                        minDate={dayjs(minCreationDate)}
                        maxDate={dayjs(maxCreationDate)}
                    />
                )}
                {minKnowledgeCutoff && maxKnowledgeCutoff && (
                    <DateRangeFilter
                        name={"Knowledge cutoff"}
                        minDate={dayjs(minKnowledgeCutoff)}
                        maxDate={dayjs(maxKnowledgeCutoff)}
                    />
                )}
                <MuiFontSans
                    style={{ height: 600, width: "100%", marginTop: "1em" }}
                >
                    <DataGrid
                        rows={models}
                        columns={columns}
                        getRowId={(row) => row.name}
                    />
                </MuiFontSans>
            </LocalizationProvider>
        </div>
    );
}

// TODO: Start hooking these inputs up to actual filter functionality
