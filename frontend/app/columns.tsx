import { CombinedModel } from "@/app/client";
import { formatTokenMillions, usageCost } from "@/app/usage-cost";
import {
    creatorLabel,
    formatNumber,
    formatParametersB,
    formatPrice,
    formatTimestamp,
} from "@/app/utility";
import { Link } from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";

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
        description: "Parameter count (billions)",
        type: "number",
        width: 90,
        valueFormatter: formatParametersB,
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
        field: "benchmark_or_coding_index",
        headerName: "Coding",
        description: "Artificial Analysis Coding Index (via OpenRouter)",
        type: "number",
        width: 100,
        valueFormatter: formatNumber,
    },
    {
        field: "benchmark_or_agentic_index",
        headerName: "Agentic",
        description: "Artificial Analysis Agentic Index (via OpenRouter)",
        type: "number",
        width: 100,
        valueFormatter: formatNumber,
    },
    {
        field: "context_length",
        headerName: "Context Length",
        type: "number",
        width: 130,
    },
    {
        field: "pricing_input",
        headerName: "Pricing Input",
        type: "number",
        width: 120,
        valueFormatter: formatPrice,
    },
    {
        field: "pricing_output",
        headerName: "Pricing Output",
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
        headerName: "Latency (ms)",
        description:
            "Median time to first token (p50, last 30 minutes) for the chosen provider",
        type: "number",
        width: 120,
        valueFormatter: formatNumber,
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
    };
}

/** Table columns, with a usage-cost column left of pricing input when a token count is set. */
export function columnsForTokenMillions(
    tokenMillions: number | undefined,
): GridColDef[] {
    if (tokenMillions === undefined) {
        return columns;
    }
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
