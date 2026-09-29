"use client";

import { useEffect, useState } from "react";
import { getMetaMetaGet } from "@/app/client";

function formatCostUsd(usd: number): string {
    return usd.toLocaleString(undefined, {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
    });
}

const REFRESH_DATE_OPTIONS: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
};

function parseRefreshDate(iso: string | null): Date | null {
    if (!iso) {
        return null;
    }
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) {
        return null;
    }
    return date;
}

function formatLocalRefresh(iso: string | null): string {
    const date = parseRefreshDate(iso);
    if (!date) {
        return "—";
    }
    return date.toLocaleString(undefined, REFRESH_DATE_OPTIONS);
}

function formatUtcRefreshTooltip(iso: string | null): string | undefined {
    const date = parseRefreshDate(iso);
    if (!date) {
        return undefined;
    }
    return date.toLocaleString(undefined, {
        ...REFRESH_DATE_OPTIONS,
        timeZone: "UTC",
        timeZoneName: "short",
    });
}

export default function MetadataNote() {
    const [loaded, setLoaded] = useState(false);
    const [costUsd, setCostUsd] = useState(0);
    const [lastRefreshAt, setLastRefreshAt] = useState<string | null>(null);

    useEffect(() => {
        getMetaMetaGet()
            .then((response) => {
                if (response.data) {
                    setCostUsd(response.data.enrichment_cost_usd);
                    setLastRefreshAt(response.data.last_refresh_at ?? null);
                }
            })
            .finally(() => {
                setLoaded(true);
            });
    }, []);

    const costDisplay = loaded ? formatCostUsd(costUsd) : "…";
    const refreshDisplay = loaded ? formatLocalRefresh(lastRefreshAt) : "…";
    const refreshUtcTitle = loaded
        ? formatUtcRefreshTooltip(lastRefreshAt)
        : undefined;

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "row",
                flexWrap: "wrap",
                alignItems: "baseline",
                gap: "0.35rem 1.25rem",
                fontSize: "0.75rem",
                lineHeight: 1.35,
                opacity: 0.85,
            }}
        >
            <span>
                <span className="font-casual">Last refresh</span>{" "}
                <span className="font-mono" title={refreshUtcTitle}>
                    {refreshDisplay}
                </span>
            </span>
            <span>
                <span className="font-casual">Enrichment cost</span>{" "}
                <span className="font-mono">{costDisplay}</span>
            </span>
        </div>
    );
}
