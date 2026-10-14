"use client";

import ModelTable from "@/app/model-table";
import { useEffect, useRef, useState } from "react";
import {
    CombinedModel,
    getMetaMetaGet,
    getModelsModelsGet,
} from "@/app/client";
import { client } from "@/app/client/client.gen";
import Titles from "@/app/titles";
import MetadataNote from "@/app/metadata-note";

client.setConfig({
    baseUrl: "/api",
});

/** Poll while the live DB is missing or a refresh is still writing the first snapshot. */
const POPULATE_POLL_MS = 15_000;

export default function Home() {
    const [models, setModels] = useState<CombinedModel[]>([]);
    const [populating, setPopulating] = useState(false);
    const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        let cancelled = false;

        const clearPoll = () => {
            if (pollTimerRef.current !== null) {
                clearTimeout(pollTimerRef.current);
                pollTimerRef.current = null;
            }
        };

        const schedulePoll = () => {
            clearPoll();
            pollTimerRef.current = setTimeout(() => {
                void load();
            }, POPULATE_POLL_MS);
        };

        const load = async () => {
            try {
                const [modelsResponse, metaResponse] = await Promise.all([
                    getModelsModelsGet(),
                    getMetaMetaGet(),
                ]);
                if (cancelled) {
                    return;
                }

                const nextModels = modelsResponse.data ?? [];
                setModels(nextModels);

                const meta = metaResponse.data;
                const databaseReady = meta?.database_ready ?? nextModels.length > 0;
                const refreshInProgress = meta?.refresh_in_progress ?? false;
                const stillPopulating =
                    nextModels.length === 0 &&
                    (!databaseReady || refreshInProgress);

                setPopulating(stillPopulating);

                if (stillPopulating) {
                    schedulePoll();
                } else {
                    clearPoll();
                }
            } catch {
                if (cancelled) {
                    return;
                }
                // Keep polling if the API is not ready yet on cold start.
                setPopulating(true);
                schedulePoll();
            }
        };

        void load();

        return () => {
            cancelled = true;
            clearPoll();
        };
    }, []);

    return (
        <div
            style={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
            }}
        >
            <div
                style={{
                    width: "100%",
                    flex: "0 0 25%",
                    overflow: "auto",
                }}
                className={"flex-center-everything"}
            >
                <Titles />
            </div>
            <div
                style={{
                    width: "80%",
                    flex: "1 1 0",
                    minHeight: 0,
                    overflow: "auto",
                    alignSelf: "center",
                }}
                className={"p-5"}
            >
                <ModelTable models={models} populating={populating} />
            </div>
            <div style={{ flex: "0 0 auto", width: "100%" }}>
                <MetadataNote />
            </div>
        </div>
    );
}
