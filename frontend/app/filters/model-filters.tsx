import CheckboxRowFilter from "@/app/filters/checkbox-row-filter";
import DateRangeFilter from "@/app/filters/date-range-filter";
import { FilterBounds, ModelFiltersState } from "@/app/filters/filter-types";
import {
    INPUT_MODALITY_OPTIONS,
    OUTPUT_MODALITY_OPTIONS,
} from "@/app/filters/modality-options";
import MultiSelectFilter from "@/app/filters/multi-select-filter";
import NumberRangeFilter from "@/app/filters/number-range-filter";
import TextFilter from "@/app/filters/text-filter";
import TokenCountField from "@/app/filters/token-count-field";
import { parseTokenMillions, usageCostStep } from "@/app/usage-cost";
import { formatLatencyMs, formatPrice, formatThroughput } from "@/app/utility";
import { FormControlLabel, FormGroup, Switch } from "@mui/material";
import dayjs from "dayjs";
import { Dispatch, SetStateAction } from "react";

interface ModelFiltersProperties {
    bounds: FilterBounds;
    filters: ModelFiltersState;
    setFilters: Dispatch<SetStateAction<ModelFiltersState>>;
    tokenMillions: string;
    onTokenMillionsChange: (value: string) => void;
}

export default function ModelFilters(
    properties: Readonly<ModelFiltersProperties>,
) {
    const {
        bounds,
        filters,
        setFilters,
        tokenMillions,
        onTokenMillionsChange,
    } = properties;
    const parsedTokenMillions = parseTokenMillions(tokenMillions);
    const usageCostBounds = bounds.usageCost;

    return (
        <div className="w-full columns-2 gap-x-16">
            <div className="w-full break-inside-avoid">
                <FormGroup sx={{ width: "100%" }}>
                    <FormControlLabel
                        sx={{
                            display: "flex",
                            maxWidth: "100%",
                            "& .MuiFormControlLabel-label": {
                                whiteSpace: "normal",
                            },
                        }}
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
                </FormGroup>
            </div>
            <TextFilter
                name="Name"
                label="Search names or families"
                value={filters.nameQuery}
                onChange={(nameQuery) => {
                    setFilters((previous) => ({
                        ...previous,
                        nameQuery,
                    }));
                }}
            />
            <div className="w-full break-inside-avoid">
                <FormGroup sx={{ width: "100%" }}>
                    <FormControlLabel
                        sx={{
                            display: "flex",
                            maxWidth: "100%",
                            "& .MuiFormControlLabel-label": {
                                whiteSpace: "normal",
                            },
                        }}
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
            </div>
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
            <div className="w-full break-inside-avoid">
                <TokenCountField
                    value={tokenMillions}
                    onChange={(value) => {
                        const nextTokens = parseTokenMillions(value);
                        if (nextTokens !== parsedTokenMillions) {
                            setFilters((previous) => ({
                                ...previous,
                                usageCost: undefined,
                            }));
                        }
                        onTokenMillionsChange(value);
                    }}
                />
                {parsedTokenMillions !== undefined && usageCostBounds && (
                    <NumberRangeFilter
                        key={parsedTokenMillions}
                        name="Cost"
                        minValue={usageCostBounds[0]}
                        maxValue={usageCostBounds[1]}
                        step={usageCostStep(
                            usageCostBounds[0],
                            usageCostBounds[1],
                        )}
                        formatValue={formatPrice}
                        onChange={(usageCost) => {
                            setFilters((previous) => ({
                                ...previous,
                                usageCost,
                            }));
                        }}
                    />
                )}
            </div>
            {bounds.pricingInput && (
                <NumberRangeFilter
                    name="Pricing input ($/1M)"
                    minValue={bounds.pricingInput[0]}
                    maxValue={bounds.pricingInput[1]}
                    step={0.01}
                    formatValue={formatPrice}
                    onChange={(pricingInput) => {
                        setFilters((previous) => ({
                            ...previous,
                            pricingInput,
                        }));
                    }}
                />
            )}
            {bounds.pricingOutput && (
                <NumberRangeFilter
                    name="Pricing output ($/1M)"
                    minValue={bounds.pricingOutput[0]}
                    maxValue={bounds.pricingOutput[1]}
                    step={0.01}
                    formatValue={formatPrice}
                    onChange={(pricingOutput) => {
                        setFilters((previous) => ({
                            ...previous,
                            pricingOutput,
                        }));
                    }}
                />
            )}
            {bounds.throughput && (
                <NumberRangeFilter
                    name="Throughput (tok/s)"
                    minValue={bounds.throughput[0]}
                    maxValue={bounds.throughput[1]}
                    step={1}
                    formatValue={formatThroughput}
                    onChange={(throughput) => {
                        setFilters((previous) => ({
                            ...previous,
                            throughput,
                        }));
                    }}
                />
            )}
            {bounds.latencyMs && (
                <NumberRangeFilter
                    name="Latency (ms)"
                    minValue={bounds.latencyMs[0]}
                    maxValue={bounds.latencyMs[1]}
                    step={1}
                    formatValue={formatLatencyMs}
                    onChange={(latencyMs) => {
                        setFilters((previous) => ({
                            ...previous,
                            latencyMs,
                        }));
                    }}
                />
            )}
            {bounds.creationDate && (
                <DateRangeFilter
                    name="Created"
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
                            knowledgeCutoff: [start.valueOf(), end.valueOf()],
                        }));
                    }}
                />
            )}
            <MultiSelectFilter
                name="Creator"
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
            <MultiSelectFilter
                name="Provider"
                label="Pick providers"
                options={bounds.providers}
                value={filters.providers}
                onChange={(providers) => {
                    setFilters((previous) => ({
                        ...previous,
                        providers,
                    }));
                }}
            />
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
        </div>
    );
}
