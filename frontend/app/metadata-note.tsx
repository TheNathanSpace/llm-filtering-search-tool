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

const metaPairStyle = {
    display: "inline-flex",
    alignItems: "baseline",
    columnGap: "0.85rem",
} as const;

const REFRESH_DATE_OPTIONS: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
};

const TWO_DAYS_MS = 2 * 24 * 60 * 60 * 1000;

const staleRefreshStyle = {
    color: "#e67e22",
    fontWeight: 700,
} as const;

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

function isRefreshOlderThanTwoDays(iso: string | null, nowMs: number): boolean {
    const date = parseRefreshDate(iso);
    if (!date) {
        return false;
    }
    return nowMs - date.getTime() > TWO_DAYS_MS;
}

export default function MetadataNote() {
    const [loaded, setLoaded] = useState(false);
    const [costUsd, setCostUsd] = useState(0);
    const [lastRefreshAt, setLastRefreshAt] = useState<string | null>(null);
    const [refreshStale, setRefreshStale] = useState(false);

    useEffect(() => {
        getMetaMetaGet()
            .then((response) => {
                if (response.data) {
                    const iso = response.data.last_refresh_at;
                    setCostUsd(response.data.enrichment_cost_usd);
                    setLastRefreshAt(iso);
                    setRefreshStale(isRefreshOlderThanTwoDays(iso, Date.now()));
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
            <span
                style={
                    loaded && refreshStale
                        ? { ...metaPairStyle, ...staleRefreshStyle }
                        : metaPairStyle
                }
            >
                <span className="font-casual" style={{ fontSize: "1.1rem" }}>
                    Last refresh:
                </span>
                <span className="font-mono" title={refreshUtcTitle}>
                    {refreshDisplay}.
                </span>
            </span>
            <span style={metaPairStyle}>
                <span className="font-casual" style={{ fontSize: "1.1rem" }}>
                    Enrichment cost:
                </span>
                <span className="font-mono">{costDisplay}.</span>
            </span>
        </div>
    );
}
