"use client";

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

function refreshTooltip(
    lastRefreshAt: string | null,
    lastEnrichmentAt: string | null,
    enrichmentInProgress: boolean,
): string | undefined {
    const refreshUtc = formatUtcRefreshTooltip(lastRefreshAt);
    const enrichmentLine = lastEnrichmentAt
        ? `Last enrichment: ${formatLocalRefresh(lastEnrichmentAt)}`
        : "Last enrichment: none";
    const waitingLine = enrichmentInProgress
        ? "Enrichment in progress."
        : "Not waiting for enrichment.";
    const lines = [
        refreshUtc ? `Refresh (UTC): ${refreshUtc}` : undefined,
        enrichmentLine,
        waitingLine,
    ].filter((line): line is string => line !== undefined);
    return lines.join("\n");
}

function isRefreshOlderThanTwoDays(iso: string | null, nowMs: number): boolean {
    const date = parseRefreshDate(iso);
    if (!date) {
        return false;
    }
    return nowMs - date.getTime() > TWO_DAYS_MS;
}

export default function MetadataNote({
    loaded,
    costUsd,
    lastRefreshAt,
    lastEnrichmentAt,
    enrichmentInProgress,
}: {
    loaded: boolean;
    costUsd: number;
    lastRefreshAt: string | null;
    lastEnrichmentAt: string | null;
    enrichmentInProgress: boolean;
}) {
    const refreshStale =
        loaded && isRefreshOlderThanTwoDays(lastRefreshAt, Date.now());
    const costDisplay = loaded ? formatCostUsd(costUsd) : "…";
    const refreshDisplay = loaded ? formatLocalRefresh(lastRefreshAt) : "…";
    const refreshUtcTitle = loaded
        ? refreshTooltip(lastRefreshAt, lastEnrichmentAt, enrichmentInProgress)
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
