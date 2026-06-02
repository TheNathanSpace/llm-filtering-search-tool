"use client";

import { Link, Typography } from "@mui/material";
import GithubLogo from "@/app/github-logo";
import ModelTable from "@/app/model-table";
import { useEffect, useState } from "react";
import { CombinedModel, getModelsModelsGet } from "@/app/client";
import { client } from "@/app/client/client.gen";

client.setConfig({
    baseUrl: "http://localhost:8000",
});

export default function Home() {
    const [models, setModels] = useState<CombinedModel[]>([]);

    useEffect(() => {
        getModelsModelsGet().then((response) => {
            if (response.data) {
                setModels(response.data);
            }
        });
    }, []);

    return (
        <div className={"flex-center-everything"}>
            <div style={{ width: "80%", textAlign: "center" }}>
                <Typography variant="h1">LLM rankings app</Typography>
                <Typography variant="h2" sx={{ marginTop: "1em" }}>
                    The goal is to consolidate multidimensional LLM metrics and
                    benchmarks into a searchable platform.
                </Typography>
                <div style={{ marginTop: "2em" }}>
                    <Link
                        href="https://github.com/TheNathanSpace/llm-filtering-search-tool"
                        color="inherit"
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
                <div style={{ marginTop: "2em" }}>
                    <ModelTable models={models} />
                </div>
            </div>
        </div>
    );
}
