"use client";

import { ThemeProvider, createTheme } from "@mui/material/styles";

const theme = createTheme({
    typography: {
        fontFamily: "var(--font-casual)",
    },
    components: {
        MuiDataGrid: {
            // https://github.com/mui/mui-x/issues/2754#issuecomment-1712564721
            styleOverrides: {
                root: {
                    "& .MuiDataGrid-cell:focus": {
                        outline: "none",
                    },
                    "& .MuiDataGrid-cell:focus-within": {
                        outline: "none",
                    },
                },
            },
        },
    },
});

export default function GlobalThemeProvider({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
