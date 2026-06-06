"use client";

import { ThemeProvider, createTheme } from "@mui/material/styles";

// eslint-disable-next-line unicorn/require-module-specifiers
import type {} from "@mui/x-data-grid/themeAugmentation";

const theme = createTheme({
    typography: {
        fontFamily: "var(--font-casual)",
        h1: {
            fontSize: "5rem",
        },
        h2: {
            fontSize: "4rem",
        },
        h3: {
            fontSize: "3rem",
        },
        h4: {
            fontSize: "2.4rem",
        },
        h5: {
            fontSize: "2rem",
        },
        h6: {
            fontSize: "1.5rem",
        },
        subtitle1: {
            fontSize: "1.3rem",
        },
        subtitle2: {
            fontSize: "1.2rem",
        },
        body1: {
            fontSize: "1rem",
        },
        body2: {
            fontSize: "0.9rem",
        },
        button: {},
        caption: {},
        overline: {},
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
