"use client";

import { Alert, AlertTitle } from "@mui/material";

export default function ExportBanner({ baseUrl }: { baseUrl: string }) {
    return (
        <Alert
            severity="warning"
            variant="filled"
            sx={{
                flex: "0 0 auto",
                marginBottom: "1rem",
                fontSize: "1.15rem",
                lineHeight: 1.45,
            }}
        >
            <AlertTitle sx={{ fontSize: "1.35rem", fontWeight: 700 }}>
                This instance is a copy of {baseUrl}
            </AlertTitle>
            Every startup downloads that instance and replaces this database and
            its caches. Remove EXPORT_BASE_URL and restart to keep this copy
            and stop downloading it again.
        </Alert>
    );
}
