import Home from "@/app/home-client";
import type { PageSearchQuery } from "@/app/filters/filter-query";

export default async function Page(properties: {
    searchParams: Promise<PageSearchQuery>;
}) {
    const initialQuery = await properties.searchParams;
    return <Home initialQuery={initialQuery} />;
}
