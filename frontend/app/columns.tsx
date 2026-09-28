import { GridColDef } from "@mui/x-data-grid";
import {
    formatCommaSeparatedList,
    formatNumber,
    formatParametersB,
    formatPrice,
    formatTimestamp,
} from "@/app/utility";
import { Link } from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";

export const columns: GridColDef[] = [
    { field: "name", headerName: "Name", width: 200 },
    { field: "creator", headerName: "Creator", width: 150 },
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
    { field: "description", headerName: "Description", width: 300 },
    {
        field: "created",
        headerName: "Created",
        width: 150,
        valueFormatter: formatTimestamp,
    },
    {
        field: "url_openrouter",
        headerName: "OpenRouter URL",
        width: 200,
        renderCell: (parameters) => {
            const value = parameters.value;
            if (!value) {
                return value;
            }
            return (
                <Link
                    className={"vertically-centered"}
                    href={value}
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    openrouter.ai <OpenInNewIcon sx={{ marginLeft: "0.5em" }} />
                </Link>
            );
        },
    },
    {
        field: "knowledge_cutoff",
        headerName: "Knowledge Cutoff",
        width: 150,
        valueFormatter: formatTimestamp,
    },
    {
        field: "context_length",
        headerName: "Context Length",
        type: "number",
        width: 130,
    },
    {
        field: "input_modalities",
        headerName: "Input Modalities",
        width: 180,
        valueFormatter: formatCommaSeparatedList,
    },
    {
        field: "output_modalities",
        headerName: "Output Modalities",
        width: 180,
        valueFormatter: formatCommaSeparatedList,
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
        field: "speed_tokens_per_second",
        headerName: "Speed (tok/s)",
        type: "number",
        width: 130,
        valueFormatter: (value: number | undefined) => {
            if (!value) {
                return "";
            }
            return value.toFixed(2);
        },
    },
    {
        field: "speed_time_to_first_token",
        headerName: "TTFT",
        description: "Time to first token",
        type: "number",
        width: 100,
    },
    {
        field: "speed_time_to_first_answer_token",
        headerName: "TTFAT",
        description: "Time to first answer token",
        type: "number",
        width: 100,
    },
];
