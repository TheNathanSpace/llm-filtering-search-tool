import { Link, Typography } from "@mui/material";
import GithubLogo from "@/app/github-logo";

export default function Titles() {
    return (
        <div style={{ textAlign: "center" }}>
            <Typography variant="h1">LLM rankings app</Typography>
            <Typography variant="h4" sx={{ marginTop: "1rem" }}>
                The goal is to consolidate multidimensional LLM metrics and
                benchmarks into a searchable platform.
            </Typography>
            <div style={{ marginTop: "2rem" }}>
                <Link
                    href="https://github.com/TheNathanSpace/llm-filtering-search-tool"
                    color="inherit"
                    className={"inline-flex"}
                    target={"_blank"}
                    rel="noopener noreferrer"
                >
                    <Typography
                        variant="h6"
                        sx={{ marginRight: "1em" }}
                        className={"font-mono!"}
                    >
                        View on GitHub
                    </Typography>
                    <GithubLogo />
                </Link>
            </div>
        </div>
    );
}
