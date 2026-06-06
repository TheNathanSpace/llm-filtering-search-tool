import { GridColDef } from "@mui/x-data-grid";
import { formatPrice, formatTimestamp } from "@/app/utility";
import { Link } from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";

export const columns: GridColDef[] = [
    { field: "name", headerName: "Name", width: 200 },
    { field: "creator", headerName: "Creator", width: 150 },
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
        field: "url_artificialanalysis",
        headerName: "Artificial Analysis URL",
        width: 200,
        renderCell: (parameters) => {
            const value = parameters.value;
            if (!value) {
                return value;
            }
            return (
                <Link href={value} target="_blank" rel="noopener noreferrer">
                    artificialanalysis.ai
                    <OpenInNewIcon sx={{ marginLeft: "0.5em" }} />
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
        type: "number",
        width: 100,
    },
    {
        field: "speed_time_to_first_answer_token",
        headerName: "TTFAT",
        type: "number",
        width: 100,
    },
    {
        field: "benchmark_artificial_analysis_intelligence_index",
        headerName: "AA Intel Index",
        type: "number",
        width: 130,
    },
    {
        field: "benchmark_artificial_analysis_coding_index",
        headerName: "AA Coding Index",
        type: "number",
        width: 130,
    },
    {
        field: "benchmark_artificial_analysis_math_index",
        headerName: "AA Math Index",
        type: "number",
        width: 130,
    },
    {
        field: "benchmark_mmlu_pro",
        headerName: "MMLU Pro",
        type: "number",
        width: 110,
    },
    { field: "benchmark_gpqa", headerName: "GPQA", type: "number", width: 100 },
    { field: "benchmark_hle", headerName: "HLE", type: "number", width: 100 },
    {
        field: "benchmark_livecodebench",
        headerName: "LiveCodeBench",
        type: "number",
        width: 140,
    },
    {
        field: "benchmark_scicode",
        headerName: "SciCode",
        type: "number",
        width: 110,
    },
    {
        field: "benchmark_math_500",
        headerName: "MATH 500",
        type: "number",
        width: 110,
    },
    { field: "benchmark_aime", headerName: "AIME", type: "number", width: 100 },
    {
        field: "benchmark_aime_25",
        headerName: "AIME 25",
        type: "number",
        width: 100,
    },
    {
        field: "benchmark_ifbench",
        headerName: "IFBench",
        type: "number",
        width: 110,
    },
    { field: "benchmark_lcr", headerName: "LCR", type: "number", width: 100 },
    {
        field: "benchmark_terminalbench_hard",
        headerName: "TerminalBench Hard",
        type: "number",
        width: 150,
    },
    { field: "benchmark_tau2", headerName: "TAU2", type: "number", width: 100 },
];
