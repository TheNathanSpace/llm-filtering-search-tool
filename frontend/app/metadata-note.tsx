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
                position: "fixed",
                bottom: "0.75rem",
                right: "0.75rem",
                zIndex: 10,
                opacity: 0.85,
            }}
        >
            <table
                style={{
                    borderCollapse: "collapse",
                    fontSize: "0.75rem",
                    lineHeight: 1.35,
                }}
            >
                <caption
                    className="font-sans"
                    style={{
                        captionSide: "top",
                        textAlign: "left",
                        paddingBottom: "0.25rem",
                        fontWeight: 600,
                    }}
                >
                    Data
                </caption>
                <thead>
                    <tr>
                        <th
                            className="font-sans"
                            scope="col"
                            style={{
                                textAlign: "left",
                                padding: "0.1rem 0.6rem 0.1rem 0",
                                fontWeight: 600,
                            }}
                        >
                            Field
                        </th>
                        <th
                            className="font-sans"
                            scope="col"
                            style={{
                                textAlign: "left",
                                padding: "0.1rem 0",
                                fontWeight: 600,
                            }}
                        >
                            Value
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td
                            className="font-casual"
                            style={{ padding: "0.1rem 0.6rem 0.1rem 0" }}
                        >
                            Enrichment cost
                        </td>
                        <td className="font-mono" style={{ padding: "0.1rem 0" }}>
                            {costDisplay}
                        </td>
                    </tr>
                    <tr>
                        <td
                            className="font-casual"
                            style={{ padding: "0.1rem 0.6rem 0.1rem 0" }}
                        >
                            Last refresh
                        </td>
                        <td
                            className="font-mono"
                            style={{ padding: "0.1rem 0" }}
                            title={refreshUtcTitle}
                        >
                            {refreshDisplay}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    );
}
