"use client";

import ModelTable from "@/app/model-table";
import { useEffect, useState } from "react";
import { CombinedModel, getModelsModelsGet } from "@/app/client";
import { client } from "@/app/client/client.gen";
import Titles from "@/app/titles";
import MetadataNote from "@/app/metadata-note";

client.setConfig({
    baseUrl: "/api",
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
        <div
            style={{ width: "100%", height: "100%" }}
            className={"flex-center-everything"}
        >
            <div
                style={{ width: "100%", height: "25%", overflow: "scroll" }}
                className={"flex-center-everything"}
            >
                <Titles />
            </div>
            <div
                style={{ width: "80%", height: "75%", overflow: "scroll" }}
                className={"p-5"}
            >
                <ModelTable models={models} />
            </div>
            <MetadataNote />
        </div>
    );
}
