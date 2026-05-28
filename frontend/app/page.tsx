"use client";

import { Link, Typography } from "@mui/material";
import GithubLogo from "@/app/github-logo";
import ModelTable from "@/app/model-table";

export default function Home() {
    return (
        <div className={"flex-center-everything"}>
            <div style={{ width: "80%", textAlign: "center" }}>
                <Typography variant="h1">LLM rankings app</Typography>
                <Typography variant="h2" sx={{ marginTop: "1em" }}>
                    The goal is to consolidate multidimensional LLM metrics and
                    benchmarks into a searchable platform.
                </Typography>
                <div
                    className={"horizontally-centered"}
                    style={{ marginTop: "2em" }}
                >
                    <Link
                        href="https://github.com/TheNathanSpace/llm-filtering-search-tool"
                        color="inherit"
                        className={"vertically-centered horizontally-centered"}
                    >
                        <Typography
                            variant="h4"
                            sx={{ marginRight: "1em" }}
                            className={"font-mono!"}
                        >
                            View on GitHub
                        </Typography>
                        <GithubLogo />
                    </Link>
                </div>
                <ModelTable />
            </div>
        </div>
    );
}
