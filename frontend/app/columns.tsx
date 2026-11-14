import { CombinedModel } from "@/app/client";
import { formatTokenMillions, usageCost } from "@/app/usage-cost";
import {
    creatorLabel,
    formatContextLength,
    formatExactPrice,
    formatLatencySeconds,
    formatNumber,
    formatParameterCount,
    formatParametersB,
    formatPrice,
    formatReadableNumber,
    formatTimestamp,
} from "@/app/utility";
import PushPinIcon from "@mui/icons-material/PushPin";
import PushPinOutlinedIcon from "@mui/icons-material/PushPinOutlined";
import { IconButton, Link, Tooltip } from "@mui/material";
import { GridColDef, GridRenderCellParams } from "@mui/x-data-grid";

export type PinColumnControls = {
    pinnedIds: ReadonlySet<string>;
    onTogglePin: (id: string) => void;
};

function pinColumn(pins: PinColumnControls): GridColDef {
    return {
        field: "pin",
        headerName: "Pin",
        width: 64,
        sortable: false,
        filterable: false,
        disableColumnMenu: true,
        align: "center",
        headerAlign: "center",
        display: "flex",
        renderCell: (parameters) => {
            const modelId = String(parameters.id);
            const pinned = pins.pinnedIds.has(modelId);
            return (
                <IconButton
                    size="small"
                    aria-label={pinned ? `Unpin ${modelId}` : `Pin ${modelId}`}
                    aria-pressed={pinned}
                    onMouseDown={(event) => {
                        event.stopPropagation();
                    }}
                    onClick={(event) => {
                        event.stopPropagation();
                        pins.onTogglePin(modelId);
                    }}
                >
                    {pinned ? (
                        <PushPinIcon fontSize="small" />
                    ) : (
                        <PushPinOutlinedIcon fontSize="small" />
                    )}
                </IconButton>
            );
        },
    };
}

/** Cell text stays the formatted value; the tooltip is `formatExact` of the stored number. */
function renderExactTooltip(
    formatExact: (value: number | undefined) => string,
) {
    return function renderTooltip(parameters: GridRenderCellParams) {
        const title = formatExact(
            typeof parameters.value === "number" ? parameters.value : undefined,
        );
        return (
            <span
                title={title === "" ? undefined : title}
                style={{
                    display: "block",
                    width: "100%",
                    height: "100%",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                }}
            >
                {parameters.formattedValue}
            </span>
        );
    };
}

const renderFullValueTooltip = renderExactTooltip(formatReadableNumber);
const renderParameterCountTooltip = renderExactTooltip(formatParameterCount);

function formatIndexPart(value: number): string {
    const formatted = formatNumber(value);
    return formatted == undefined ? "" : String(formatted);
}

/** `FrontierCode 2.0 / Terminal-Bench 4.0: 46.4 / 59.6` when both inputs are stored. */
function codingBreakdown(row: CombinedModel): string | undefined {
    const frontier = row.benchmark_coding_frontier;
    const terminal = row.benchmark_coding_terminal;
    if (typeof frontier !== "number" || typeof terminal !== "number") {
        return undefined;
    }
    return (
        "FrontierCode 2.0 / Terminal-Bench 4.0: " +
        `${formatIndexPart(frontier)} / ${formatIndexPart(terminal)}`
    );
}

export const columns: GridColDef[] = [
    {
        field: "name",
        headerName: "Name",
        width: 200,
        renderCell: (parameters) => {
            const name = parameters.value;
            const url = parameters.row.url_openrouter;
            if (!name || !url) {
                return name;
            }
            return (
                <Link href={url} target="_blank" rel="noopener noreferrer">
                    {name}
                </Link>
            );
        },
    },
    {
        field: "is_open_weights",
        headerName: "Open Weights",
        type: "boolean",
        width: 120,
    },
    {
        field: "parameters_b",
        headerName: "Size",
        description:
            "Thousands through 900,000 parameters (400k); millions through 900 million (500M); billions through 900 billion (410B); trillions above that (1T). 100-900 of a unit rounds to the nearest 10",
        type: "number",
        width: 90,
        valueFormatter: formatParametersB,
        renderCell: renderParameterCountTooltip,
    },
    {
        field: "benchmark_or_intelligence_index",
        headerName: "Intelligence",
        description: "Artificial Analysis Intelligence Index (via OpenRouter)",
        type: "number",
        width: 120,
        valueFormatter: formatNumber,
    },
    {
        field: "benchmark_coding",
        headerName: "Coding",
        description: "60% FrontierCode 2.0 and 40% Terminal-Bench 4.0",
        type: "number",
        width: 100,
        valueFormatter: formatNumber,
        renderCell: (parameters) => {
            const title = codingBreakdown(parameters.row);
            if (!title) {
                return parameters.formattedValue;
            }
            return (
                <Tooltip
                    title={title}
                    slotProps={{
                        tooltip: {
                            sx: { maxWidth: "none", whiteSpace: "nowrap" },
                        },
                    }}
                >
                    <span
                        style={{
                            display: "block",
                            width: "100%",
                            height: "100%",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                        }}
                    >
                        {parameters.formattedValue}
                    </span>
                </Tooltip>
            );
        },
    },
    {
        field: "context_length",
        headerName: "Context Length",
        description:
            "Thousands through 900,000 tokens (130k; 100-900 of the unit rounds to the nearest 10); millions above that (1M)",
        type: "number",
        width: 130,
        valueFormatter: formatContextLength,
        renderCell: renderFullValueTooltip,
    },
    {
        field: "pricing_input",
        headerName: "Input Cost",
        description:
            "Listed price per million input tokens for the chosen provider",
        type: "number",
        width: 120,
        valueFormatter: formatPrice,
    },
    {
        field: "pricing_output",
        headerName: "Output Cost",
        description:
            "Listed price per million output tokens for the chosen provider",
        type: "number",
        width: 120,
        valueFormatter: formatPrice,
    },
    {
        field: "throughput",
        headerName: "Throughput",
        description:
            "Median output tokens/sec (p50, last 30 minutes) for the chosen provider",
        type: "number",
        width: 120,
        valueFormatter: formatNumber,
    },
    {
        field: "latency_ms",
        headerName: "Latency",
        description:
            "Median time to first token in seconds (p50, last 30 minutes) for the chosen provider",
        type: "number",
        width: 120,
        valueFormatter: formatLatencySeconds,
        renderCell: renderFullValueTooltip,
    },
    {
        field: "created",
        headerName: "Created",
        width: 150,
        valueFormatter: formatTimestamp,
    },
    {
        field: "knowledge_cutoff",
        headerName: "Knowledge Cutoff",
        width: 150,
        valueFormatter: formatTimestamp,
    },
    {
        field: "creator",
        headerName: "Creator",
        width: 150,
        valueGetter: (_value, row) => creatorLabel(row.creator, row.name),
    },
];

function usageCostColumn(tokenMillions: number): GridColDef<CombinedModel> {
    const amount = formatTokenMillions(tokenMillions);
    return {
        field: "usage_cost",
        headerName: `Cost (${amount}M)`,
        description: `Listed cost of ${amount} million tokens for the chosen provider (90% input / 10% output)`,
        type: "number",
        width: 130,
        valueGetter: (_value, row) =>
            usageCost(tokenMillions, row.pricing_input, row.pricing_output),
        valueFormatter: formatPrice,
        renderCell: renderExactTooltip(formatExactPrice),
    };
}

/** Table columns, with a usage-cost column left of input cost when a token count is set. */
export function columnsForTokenMillions(
    tokenMillions: number | undefined,
    pins: PinColumnControls,
): GridColDef[] {
    const dataColumns =
        tokenMillions === undefined
            ? columns
            : columnsWithUsageCost(tokenMillions);
    return [pinColumn(pins), ...dataColumns];
}

function columnsWithUsageCost(tokenMillions: number): GridColDef[] {
    const pricingIndex = columns.findIndex(
        (column) => column.field === "pricing_input",
    );
    const costColumn = usageCostColumn(tokenMillions);
    return [
        ...columns.slice(0, pricingIndex),
        costColumn,
        ...columns.slice(pricingIndex),
    ];
}
