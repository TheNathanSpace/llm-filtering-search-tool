import FilterOption from "@/app/filters/filter-option";
import { Slider, TextField, Typography } from "@mui/material";
import { MuiFontSans } from "@/app/mui-font";
import { useRef, useState, type KeyboardEvent } from "react";
import { formatNumber } from "@/app/utility";

interface NumberRangeFilterProperties {
    name: string;
    minValue: number;
    maxValue: number;
    defaultStart?: number;
    defaultEnd?: number;
    onChange?: (range: [number, number]) => void;
    step?: number;
    /** Label formatter for the slider thumb and the range text under the control. */
    formatValue?: (value: number) => string;
}

type RangeEndpointName = "start" | "end";

function formatDraft(value: number): string {
    const rounded = Math.round((value + Number.EPSILON) * 1e6) / 1e6;
    return String(rounded);
}

/** Accept a typed number, including thousands separators or a trailing B/$ the label may suggest. */
function parseTypedNumber(text: string): number | undefined {
    let normalized = text.trim().replaceAll(",", "").replaceAll("$", "");
    if (normalized.endsWith("B") || normalized.endsWith("b")) {
        normalized = normalized.slice(0, -1).trim();
    }
    if (normalized === "") {
        return undefined;
    }
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) {
        return undefined;
    }
    return parsed;
}

function applyTypedEndpoint(
    current: readonly [number, number],
    endpoint: RangeEndpointName,
    typed: number,
    minimum: number,
    maximum: number,
): [number, number] {
    const clamped = Math.min(maximum, Math.max(minimum, typed));
    if (endpoint === "start") {
        return [clamped, Math.max(current[1], clamped)];
    }
    return [Math.min(current[0], clamped), clamped];
}

interface RangeEndpointEditorProperties {
    initialDraft: string;
    ariaLabel: string;
    onCommit: (next: number) => void;
    onClose: () => void;
}

function RangeEndpointEditor(
    properties: Readonly<RangeEndpointEditorProperties>,
) {
    const [draft, setDraft] = useState(properties.initialDraft);
    const cancelled = useRef(false);

    function commitDraft(text: string) {
        if (cancelled.current) {
            return;
        }
        const parsed = parseTypedNumber(text);
        if (parsed !== undefined) {
            properties.onCommit(parsed);
        }
        properties.onClose();
    }

    return (
        <TextField
            variant="standard"
            size="small"
            autoFocus
            value={draft}
            onChange={(event) => {
                setDraft(event.target.value);
            }}
            onFocus={(event) => {
                event.target.select();
            }}
            onBlur={(event) => {
                commitDraft(event.target.value);
            }}
            slotProps={{
                htmlInput: {
                    "aria-label": properties.ariaLabel,
                    inputMode: "decimal",
                    autoComplete: "off",
                    onKeyDown: (event: KeyboardEvent<HTMLInputElement>) => {
                        if (event.key === "Enter") {
                            event.preventDefault();
                            commitDraft(event.currentTarget.value);
                        } else if (event.key === "Escape") {
                            event.preventDefault();
                            cancelled.current = true;
                            properties.onClose();
                        }
                    },
                },
            }}
            sx={{
                width: "7.5rem",
                "& .MuiInputBase-input": {
                    textAlign: "center",
                    fontSize: "0.875rem",
                    padding: "0 0 1px",
                },
            }}
        />
    );
}

interface RangeEndpointProperties {
    label: string;
    value: number;
    ariaLabel: string;
    active: boolean;
    onActivate: () => void;
    onCommit: (next: number) => void;
    onClose: () => void;
}

function RangeEndpoint(properties: Readonly<RangeEndpointProperties>) {
    if (!properties.active) {
        return (
            <Typography
                component="button"
                type="button"
                variant="body2"
                aria-label={properties.ariaLabel}
                title="Click to type a value"
                onClick={properties.onActivate}
                sx={{
                    border: 0,
                    margin: 0,
                    padding: 0,
                    background: "transparent",
                    color: "inherit",
                    font: "inherit",
                    lineHeight: 1.2,
                    cursor: "text",
                    textDecoration: "underline",
                    textDecorationStyle: "dotted",
                    textUnderlineOffset: "0.15em",
                }}
            >
                {properties.label}
            </Typography>
        );
    }

    return (
        <RangeEndpointEditor
            initialDraft={formatDraft(properties.value)}
            ariaLabel={properties.ariaLabel}
            onCommit={properties.onCommit}
            onClose={properties.onClose}
        />
    );
}

export default function NumberRangeFilter(
    properties: Readonly<NumberRangeFilterProperties>,
) {
    const initialStart = properties.defaultStart ?? properties.minValue;
    const initialEnd = properties.defaultEnd ?? properties.maxValue;
    const formatValue = properties.formatValue ?? formatNumber;

    const [value, setValue] = useState<number[]>([initialStart, initialEnd]);
    const [activeEndpoint, setActiveEndpoint] = useState<
        RangeEndpointName | undefined
    >();

    function publish(next: [number, number]) {
        setValue(next);
        properties.onChange?.(next);
    }

    const handleChange = (_event: Event, newValue: number | number[]) => {
        const numeric = newValue as number[];
        publish([numeric[0], numeric[1]]);
    };

    function commitEndpoint(endpoint: RangeEndpointName, typed: number) {
        publish(
            applyTypedEndpoint(
                [value[0], value[1]],
                endpoint,
                typed,
                properties.minValue,
                properties.maxValue,
            ),
        );
    }

    return (
        <FilterOption name={properties.name}>
            <MuiFontSans>
                <Slider
                    value={value}
                    onChange={handleChange}
                    valueLabelDisplay="auto"
                    valueLabelFormat={formatValue}
                    min={properties.minValue}
                    max={properties.maxValue}
                    step={properties.step ?? 100}
                    getAriaLabel={(index) =>
                        index === 0
                            ? `${properties.name} minimum`
                            : `${properties.name} maximum`
                    }
                />
                <Typography
                    variant="body2"
                    component="div"
                    sx={{
                        mt: -1,
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        gap: 0.75,
                        lineHeight: 1.2,
                        minHeight: "1.5rem",
                    }}
                >
                    <RangeEndpoint
                        label={String(formatValue(value[0]) ?? "")}
                        value={value[0]}
                        ariaLabel={`${properties.name} minimum, click to type a value`}
                        active={activeEndpoint === "start"}
                        onActivate={() => {
                            setActiveEndpoint("start");
                        }}
                        onClose={() => {
                            setActiveEndpoint(undefined);
                        }}
                        onCommit={(typed) => {
                            commitEndpoint("start", typed);
                        }}
                    />
                    <span aria-hidden="true">–</span>
                    <RangeEndpoint
                        label={String(formatValue(value[1]) ?? "")}
                        value={value[1]}
                        ariaLabel={`${properties.name} maximum, click to type a value`}
                        active={activeEndpoint === "end"}
                        onActivate={() => {
                            setActiveEndpoint("end");
                        }}
                        onClose={() => {
                            setActiveEndpoint(undefined);
                        }}
                        onCommit={(typed) => {
                            commitEndpoint("end", typed);
                        }}
                    />
                </Typography>
            </MuiFontSans>
        </FilterOption>
    );
}
