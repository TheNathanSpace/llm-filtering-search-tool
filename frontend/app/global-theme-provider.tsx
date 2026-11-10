"use client";

import { blue } from "@mui/material/colors";
import { ThemeProvider, createTheme } from "@mui/material/styles";

// eslint-disable-next-line unicorn/require-module-specifiers
import type {} from "@mui/x-data-grid/themeAugmentation";

const theme = createTheme({
    palette: {
        primary: {
            main: "#917aff",
        },
    },
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
        MuiLink: {
            defaultProps: {
                color: blue[700],
            },
        },
        MuiTooltip: {
            styleOverrides: {
                tooltip: {
                    backgroundColor: "#fff",
                    color: "#000",
                    fontFamily: "var(--font-sans)",
                    fontSize: "1rem",
                    fontWeight: 400,
                    lineHeight: 1.35,
                    border: "1px solid #917aff",
                    borderRadius: 4,
                    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.28)",
                    padding: "6px 10px",
                    maxWidth: 480,
                },
                arrow: {
                    color: "#fff",
                },
            },
        },
        MuiDataGrid: {
            // https://github.com/mui/mui-x/issues/2754#issuecomment-1712564721
            styleOverrides: {
                root: {
                    "& .MuiDataGrid-cell:focus": {
                        outline: "none !important",
                    },
                    "& .MuiDataGrid-cell:focus-within": {
                        outline: "none !important",
                    },
                    "& .MuiDataGrid-columnHeader:focus": {
                        outline: "none !important",
                    },
                    "& .MuiDataGrid-columnHeader:focus-within": {
                        outline: "none !important",
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
