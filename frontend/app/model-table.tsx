import { DataGrid } from "@mui/x-data-grid";
import { CombinedModel } from "./client";
import { MuiFontSans } from "@/app/mui-font";
import { Autocomplete, Chip, TextField } from "@mui/material";
import { columns } from "@/app/columns";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import FilterOption from "@/app/filter-option";
import DateRangeFilter from "@/app/date-range-filter";
import dayjs, { Dayjs } from "dayjs";

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

    /**
     * Compute the minimum and maximum creation timestamps from the provided models.
     * The `created` field is a Unix timestamp in seconds (or null). The function
     * returns a tuple of Dayjs objects representing the earliest and latest dates.
     * If no valid timestamps are found, the current date is used for both values.
     */
    // Generic helper to compute min and max timestamps for any numeric field on CombinedModel.
    function getMinMaxDates(
        models: CombinedModel[],
        selector: (model: CombinedModel) => number | null | undefined,
    ): [Dayjs, Dayjs] {
        const timestamps = models
            .map((model) => selector(model))
            .filter((t): t is number => typeof t === "number" && t !== null);

        if (timestamps.length === 0) {
            const now = dayjs();
            return [now, now];
        }

        const min = Math.min(...timestamps);
        const max = Math.max(...timestamps);
        // Convert seconds to milliseconds for Dayjs
        return [dayjs(min * 1000), dayjs(max * 1000)];
    }

    /**
     * Compute the minimum and maximum knowledge cutoff timestamps from the models.
     */
    const [minCreationDate, maxCreationDate] = getMinMaxDates(
        models,
        (model) => model.created,
    );
    const [minKnowledgeCutoff, maxKnowledgeCutoff] = getMinMaxDates(
        models,
        (model) => model.knowledge_cutoff,
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
                <DateRangeFilter
                    name={"Creation date"}
                    minDate={dayjs(minCreationDate)}
                    maxDate={dayjs(maxCreationDate)}
                />
                <DateRangeFilter
                    name={"Knowledge cutoff"}
                    minDate={dayjs(minKnowledgeCutoff)}
                    maxDate={dayjs(maxKnowledgeCutoff)}
                />
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
