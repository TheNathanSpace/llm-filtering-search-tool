import CheckboxRowFilter from "@/app/filters/checkbox-row-filter";
import DateRangeFilter from "@/app/filters/date-range-filter";
import {
    createInitialUserChoices,
    FilterBounds,
    ModelFiltersState,
    NumberRange,
    resolveFilters,
} from "@/app/filters/filter-types";
import {
    INPUT_MODALITY_OPTIONS,
    OUTPUT_MODALITY_OPTIONS,
} from "@/app/filters/modality-options";
import MultiSelectFilter from "@/app/filters/multi-select-filter";
import NumberRangeFilter from "@/app/filters/number-range-filter";
import TextFilter from "@/app/filters/text-filter";
import TokenCountField from "@/app/filters/token-count-field";
import { parseTokenMillions, usageCostStep } from "@/app/usage-cost";
import { MuiFontCasual } from "@/app/mui-font";
import {
    formatContextLength,
    formatLatencySeconds,
    formatPrice,
    formatThroughput,
    parseContextLength,
    parseLatencySeconds,
} from "@/app/utility";
import { Button, FormControlLabel, FormGroup, Switch } from "@mui/material";
import dayjs from "dayjs";
import { Dispatch, SetStateAction, useState } from "react";

/** Keep a shared range inside the slider's min/max so a restored URL cannot break it. */
function rangeDefaults(
    range: NumberRange | undefined,
    bounds: NumberRange,
): { defaultStart: number; defaultEnd: number } {
    const clamp = (value: number) =>
        Math.min(bounds[1], Math.max(bounds[0], value));
    const start = clamp(range?.[0] ?? bounds[0]);
    const end = clamp(range?.[1] ?? bounds[1]);
    return {
        defaultStart: Math.min(start, end),
        defaultEnd: Math.max(start, end),
    };
}

function dateDefaults(range: NumberRange | undefined, bounds: NumberRange) {
    const defaults = rangeDefaults(range, bounds);
    return {
        defaultStart: dayjs(defaults.defaultStart),
        defaultEnd: dayjs(defaults.defaultEnd),
    };
}

interface ModelFiltersProperties {
    bounds: FilterBounds;
    filters: ModelFiltersState;
    setFilters: Dispatch<SetStateAction<ModelFiltersState>>;
    tokenMillions: string;
    onTokenMillionsChange: (value: string) => void;
    onClearPins: () => void;
}

const panelButtonSx = {
    textTransform: "none",
    whiteSpace: "nowrap",
    fontSize: "1rem",
    lineHeight: 1.15,
    color: "inherit",
    borderColor: "primary.main",
    "&:hover": {
        color: "inherit",
        borderColor: "primary.main",
    },
} as const;

function PanelButton({
    label,
    onClick,
}: {
    label: string;
    onClick: () => void;
}) {
    return (
        <div className="w-full break-inside-avoid px-1 pt-2 pb-4">
            <MuiFontCasual style={{ width: "100%" }}>
                <Button
                    variant="outlined"
                    color="primary"
                    fullWidth
                    onClick={onClick}
                    sx={panelButtonSx}
                >
                    {label}
                </Button>
            </MuiFontCasual>
        </div>
    );
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
        onClearPins,
    } = properties;
    const [rangeRevision, setRangeRevision] = useState(0);
    const parsedTokenMillions = parseTokenMillions(tokenMillions);
    const usageCostBounds = bounds.usageCost;

    function resetFilters() {
        setFilters(resolveFilters(createInitialUserChoices(), bounds));
        onTokenMillionsChange("");
        setRangeRevision((revision) => revision + 1);
    }

    return (
        <div className="w-full columns-2 gap-x-16">
            <PanelButton
                label="Reset all of these dang filters"
                onClick={resetFilters}
            />
            <PanelButton label="Clear pins" onClick={onClearPins} />
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
                                checked={filters.pinnedOnly}
                                onChange={(_event, checked) => {
                                    setFilters((previous) => ({
                                        ...previous,
                                        pinnedOnly: checked,
                                    }));
                                }}
                            />
                        }
                        label="Hide unpinned models"
                    />
                </FormGroup>
            </div>
            <TextFilter
                name="Name"
                label="Search names or slugs"
                value={filters.nameQuery}
                resizable
                help={
                    "Matches display names and OpenRouter slugs (e.g. gpt-5-nano).\n" +
                    "Punctuation is ignored, so gpt 5 matches GPT-5.\n" +
                    "A number matches that whole number, including inside a word: 4.1 matches v4.1, and 5 does not match 5.5.\n" +
                    "Commas OR alternatives: gpt 5, deepseek v4.1\n" +
                    "A leading minus excludes matches: -nano"
                }
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
                    key={`parametersB-${rangeRevision}`}
                    name="Size (B params)"
                    minValue={bounds.parametersB[0]}
                    maxValue={bounds.parametersB[1]}
                    {...rangeDefaults(filters.parametersB, bounds.parametersB)}
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
                    key={`intelligence-${rangeRevision}`}
                    name="Intelligence"
                    minValue={bounds.intelligenceIndex[0]}
                    maxValue={bounds.intelligenceIndex[1]}
                    {...rangeDefaults(
                        filters.intelligenceIndex,
                        bounds.intelligenceIndex,
                    )}
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
                    key={`coding-${rangeRevision}`}
                    name="Coding"
                    minValue={bounds.codingIndex[0]}
                    maxValue={bounds.codingIndex[1]}
                    {...rangeDefaults(filters.codingIndex, bounds.codingIndex)}
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
                    key={`agentic-${rangeRevision}`}
                    name="Agentic"
                    minValue={bounds.agenticIndex[0]}
                    maxValue={bounds.agenticIndex[1]}
                    {...rangeDefaults(
                        filters.agenticIndex,
                        bounds.agenticIndex,
                    )}
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
                    key={`context-${rangeRevision}`}
                    name="Context length"
                    minValue={bounds.contextLength[0]}
                    maxValue={bounds.contextLength[1]}
                    {...rangeDefaults(
                        filters.contextLength,
                        bounds.contextLength,
                    )}
                    formatValue={formatContextLength}
                    formatDraft={formatContextLength}
                    parseDraft={parseContextLength}
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
                        key={`cost-${parsedTokenMillions}-${rangeRevision}`}
                        name="Cost"
                        minValue={usageCostBounds[0]}
                        maxValue={usageCostBounds[1]}
                        {...rangeDefaults(filters.usageCost, usageCostBounds)}
                        step={usageCostStep(
                            usageCostBounds[0],
                            usageCostBounds[1],
                        )}
                        formatValue={formatPrice}
                        help="Dollar cost of the token count above, using the 90% input / 10% output blend."
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
                    key={`pricingInput-${rangeRevision}`}
                    name="Pricing input ($/1M)"
                    minValue={bounds.pricingInput[0]}
                    maxValue={bounds.pricingInput[1]}
                    {...rangeDefaults(
                        filters.pricingInput,
                        bounds.pricingInput,
                    )}
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
                    key={`pricingOutput-${rangeRevision}`}
                    name="Pricing output ($/1M)"
                    minValue={bounds.pricingOutput[0]}
                    maxValue={bounds.pricingOutput[1]}
                    {...rangeDefaults(
                        filters.pricingOutput,
                        bounds.pricingOutput,
                    )}
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
                    key={`throughput-${rangeRevision}`}
                    name="Throughput (tok/s)"
                    minValue={bounds.throughput[0]}
                    maxValue={bounds.throughput[1]}
                    {...rangeDefaults(filters.throughput, bounds.throughput)}
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
                    key={`latency-${rangeRevision}`}
                    name="Latency"
                    minValue={bounds.latencyMs[0]}
                    maxValue={bounds.latencyMs[1]}
                    {...rangeDefaults(filters.latencyMs, bounds.latencyMs)}
                    step={1}
                    formatValue={formatLatencySeconds}
                    formatDraft={formatLatencySeconds}
                    parseDraft={parseLatencySeconds}
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
                    key={`created-${rangeRevision}`}
                    name="Created"
                    minDate={dayjs(bounds.creationDate[0])}
                    maxDate={dayjs(bounds.creationDate[1])}
                    {...dateDefaults(filters.creationDate, bounds.creationDate)}
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
                    key={`cutoff-${rangeRevision}`}
                    name="Knowledge cutoff"
                    minDate={dayjs(bounds.knowledgeCutoff[0])}
                    maxDate={dayjs(bounds.knowledgeCutoff[1])}
                    {...dateDefaults(
                        filters.knowledgeCutoff,
                        bounds.knowledgeCutoff,
                    )}
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
