import CheckboxRowFilter from "@/app/filters/checkbox-row-filter";
import DateRangeFilter from "@/app/filters/date-range-filter";
import { FilterBounds, ModelFiltersState } from "@/app/filters/filter-types";
import {
    INPUT_MODALITY_OPTIONS,
    OUTPUT_MODALITY_OPTIONS,
} from "@/app/filters/modality-options";
import MultiSelectFilter from "@/app/filters/multi-select-filter";
import NumberRangeFilter from "@/app/filters/number-range-filter";
import { FormControlLabel, FormGroup, Grid, Switch } from "@mui/material";
import dayjs from "dayjs";
import { Dispatch, SetStateAction } from "react";

interface ModelFiltersProperties {
    bounds: FilterBounds;
    filters: ModelFiltersState;
    setFilters: Dispatch<SetStateAction<ModelFiltersState>>;
}

export default function ModelFilters(
    properties: Readonly<ModelFiltersProperties>,
) {
    const { bounds, filters, setFilters } = properties;

    return (
        <Grid container spacing={10}>
            <Grid size={6}>
                <FormGroup sx={{ width: "max-content" }}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={filters.includeMissing}
                                onChange={(_event, checked) => {
                                    setFilters((previous) => ({
                                        ...previous,
                                        includeMissing: checked,
                                    }));
                                }}
                            />
                        }
                        label="Treat entries with missing values as included in filters"
                    />
                    <FormControlLabel
                        control={
                            <Switch
                                checked={filters.openWeightsOnly}
                                onChange={(_event, checked) => {
                                    setFilters((previous) => ({
                                        ...previous,
                                        openWeightsOnly: checked,
                                    }));
                                }}
                            />
                        }
                        label="Open weights only"
                    />
                </FormGroup>
                {bounds.intelligenceIndex && (
                    <NumberRangeFilter
                        name="Intelligence"
                        minValue={bounds.intelligenceIndex[0]}
                        maxValue={bounds.intelligenceIndex[1]}
                        step={0.1}
                        onChange={(intelligenceIndex) => {
                            setFilters((previous) => ({
                                ...previous,
                                intelligenceIndex,
                            }));
                        }}
                    />
                )}
                {bounds.codingIndex && (
                    <NumberRangeFilter
                        name="Coding"
                        minValue={bounds.codingIndex[0]}
                        maxValue={bounds.codingIndex[1]}
                        step={0.1}
                        onChange={(codingIndex) => {
                            setFilters((previous) => ({
                                ...previous,
                                codingIndex,
                            }));
                        }}
                    />
                )}
                {bounds.agenticIndex && (
                    <NumberRangeFilter
                        name="Agentic"
                        minValue={bounds.agenticIndex[0]}
                        maxValue={bounds.agenticIndex[1]}
                        step={0.1}
                        onChange={(agenticIndex) => {
                            setFilters((previous) => ({
                                ...previous,
                                agenticIndex,
                            }));
                        }}
                    />
                )}
                <MultiSelectFilter
                    name="Creators"
                    label="Pick creators"
                    options={bounds.creators}
                    value={filters.creators}
                    onChange={(creators) => {
                        setFilters((previous) => ({
                            ...previous,
                            creators,
                        }));
                    }}
                />
                {bounds.creationDate && (
                    <DateRangeFilter
                        name="Creation date"
                        minDate={dayjs(bounds.creationDate[0])}
                        maxDate={dayjs(bounds.creationDate[1])}
                        onChange={([start, end]) => {
                            setFilters((previous) => ({
                                ...previous,
                                creationDate: [start.valueOf(), end.valueOf()],
                            }));
                        }}
                    />
                )}
                {bounds.knowledgeCutoff && (
                    <DateRangeFilter
                        name="Knowledge cutoff"
                        minDate={dayjs(bounds.knowledgeCutoff[0])}
                        maxDate={dayjs(bounds.knowledgeCutoff[1])}
                        onChange={([start, end]) => {
                            setFilters((previous) => ({
                                ...previous,
                                knowledgeCutoff: [
                                    start.valueOf(),
                                    end.valueOf(),
                                ],
                            }));
                        }}
                    />
                )}
                {bounds.contextLength && (
                    <NumberRangeFilter
                        name="Context length"
                        minValue={bounds.contextLength[0]}
                        maxValue={bounds.contextLength[1]}
                        onChange={(contextLength) => {
                            setFilters((previous) => ({
                                ...previous,
                                contextLength,
                            }));
                        }}
                    />
                )}
                {bounds.parametersB && (
                    <NumberRangeFilter
                        name="Size (B params)"
                        minValue={bounds.parametersB[0]}
                        maxValue={bounds.parametersB[1]}
                        step={0.1}
                        onChange={(parametersB) => {
                            setFilters((previous) => ({
                                ...previous,
                                parametersB,
                            }));
                        }}
                    />
                )}
            </Grid>
            <Grid size={6}>
                <CheckboxRowFilter
                    name="Input modalities"
                    options={INPUT_MODALITY_OPTIONS}
                    value={filters.inputModalities}
                    onChange={(inputModalities) => {
                        setFilters((previous) => ({
                            ...previous,
                            inputModalities,
                        }));
                    }}
                />
                <CheckboxRowFilter
                    name="Output modalities"
                    options={OUTPUT_MODALITY_OPTIONS}
                    value={filters.outputModalities}
                    onChange={(outputModalities) => {
                        setFilters((previous) => ({
                            ...previous,
                            outputModalities,
                        }));
                    }}
                />
            </Grid>
        </Grid>
    );
}
