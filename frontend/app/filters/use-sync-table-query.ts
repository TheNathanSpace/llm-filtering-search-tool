"use client";

import {
    serializeTableQuery,
    TableQueryState,
} from "@/app/filters/filter-query";
import { useEffect } from "react";

/**
 * Keep the address bar aligned with the table setup.
 * Passing the current history entry (it carries Next's `__NA` marker) updates
 * the URL in place and does not navigate or add a history entry.
 */
export function useSyncTableQuery(state: TableQueryState): void {
    const query = serializeTableQuery(state);

    useEffect(() => {
        const nextUrl = new URL(globalThis.location.href);
        nextUrl.search = query;
        if (nextUrl.href === globalThis.location.href) {
            return;
        }
        const next = `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`;
        globalThis.history.replaceState(globalThis.history.state, "", next);
    }, [query]);
}
