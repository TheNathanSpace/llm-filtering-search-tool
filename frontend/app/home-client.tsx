"use client";

import ModelTable from "@/app/model-table";
import { useEffect, useRef, useState } from "react";
import {
    CombinedModel,
    getMetaMetaGet,
    getModelsModelsGet,
} from "@/app/client";
import { client } from "@/app/client/client.gen";
import type { PageSearchQuery } from "@/app/filters/filter-query";
import Titles from "@/app/titles";
import MetadataNote from "@/app/metadata-note";
import ExportBanner from "@/app/export-banner";

client.setConfig({
    baseUrl: "/api",
});

/** Poll models while a refresh or enrichment run is writing rows. */
const ACTIVE_POLL_MS = 15_000;
/** Poll metadata while the page is idle so the footer can show a new run. */
const META_POLL_MS = 60_000;

export default function Home({
    initialQuery,
}: {
    initialQuery: PageSearchQuery;
}) {
    const [models, setModels] = useState<CombinedModel[]>([]);
    const [populating, setPopulating] = useState(false);
    const [metaLoaded, setMetaLoaded] = useState(false);
    const [costUsd, setCostUsd] = useState(0);
    const [lastRefreshAt, setLastRefreshAt] = useState<string | null>(null);
    const [lastEnrichmentAt, setLastEnrichmentAt] = useState<string | null>(
        null,
    );
    const [enrichmentInProgress, setEnrichmentInProgress] = useState(false);
    const [exportBaseUrl, setExportBaseUrl] = useState<string | undefined>();
    const pollTimerReference = useRef<
        ReturnType<typeof setTimeout> | undefined
    >(undefined);
    const modelCountReference = useRef(0);
    const refreshSeenReference = useRef<string | null | undefined>(undefined);
    const enrichmentSeenReference = useRef<string | null | undefined>(
        undefined,
    );

    useEffect(() => {
        let cancelled = false;

        const clearPoll = () => {
            if (pollTimerReference.current !== undefined) {
                clearTimeout(pollTimerReference.current);
                pollTimerReference.current = undefined;
            }
        };

        const schedulePoll = (delayMs: number, includeModels: boolean) => {
            clearPoll();
            pollTimerReference.current = setTimeout(() => {
                void load(includeModels);
            }, delayMs);
        };

        const load = async (includeModels: boolean) => {
            try {
                const metaResponse = await getMetaMetaGet();
                const modelsResponse = includeModels
                    ? await getModelsModelsGet()
                    : null;
                if (cancelled) {
                    return;
                }

                const meta = metaResponse.data;
                if (meta) {
                    const refreshChanged =
                        refreshSeenReference.current !== undefined &&
                        refreshSeenReference.current !== meta.last_refresh_at;
                    const enrichmentChanged =
                        enrichmentSeenReference.current !== undefined &&
                        enrichmentSeenReference.current !==
                            meta.last_enrichment_completed_at;
                    refreshSeenReference.current = meta.last_refresh_at;
                    enrichmentSeenReference.current =
                        meta.last_enrichment_completed_at;
                    setMetaLoaded(true);
                    setCostUsd(meta.enrichment_cost_usd);
                    setLastRefreshAt(meta.last_refresh_at);
                    setLastEnrichmentAt(meta.last_enrichment_completed_at);
                    setEnrichmentInProgress(meta.enrichment_in_progress);
                    setExportBaseUrl(meta.export_base_url || undefined);
                    if (
                        (refreshChanged || enrichmentChanged) &&
                        !includeModels
                    ) {
                        void load(true);
                        return;
                    }
                }

                const nextModels = modelsResponse?.data;
                if (nextModels) {
                    setModels(nextModels);
                    modelCountReference.current = nextModels.length;
                }
                const modelCount =
                    nextModels?.length ?? modelCountReference.current;

                const databaseReady = meta?.database_ready ?? modelCount > 0;
                const refreshInProgress = meta?.refresh_in_progress ?? false;
                const enrichmentActive = meta?.enrichment_in_progress ?? false;
                const stillPopulating =
                    modelCount === 0 && (!databaseReady || refreshInProgress);
                const jobActive =
                    stillPopulating || refreshInProgress || enrichmentActive;

                setPopulating(stillPopulating);
                schedulePoll(
                    jobActive ? ACTIVE_POLL_MS : META_POLL_MS,
                    jobActive,
                );
            } catch {
                if (cancelled) {
                    return;
                }
                // Keep polling if the API is not ready yet on cold start.
                setPopulating(true);
                schedulePoll(ACTIVE_POLL_MS, true);
            }
        };

        void load(true);

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
            {exportBaseUrl && <ExportBanner baseUrl={exportBaseUrl} />}
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
                <ModelTable
                    models={models}
                    populating={populating}
                    initialQuery={initialQuery}
                />
            </div>
            <div style={{ flex: "0 0 auto", width: "100%" }}>
                <MetadataNote
                    loaded={metaLoaded}
                    costUsd={costUsd}
                    lastRefreshAt={lastRefreshAt}
                    lastEnrichmentAt={lastEnrichmentAt}
                    enrichmentInProgress={enrichmentInProgress}
                />
            </div>
        </div>
    );
}
