"use client";

import { ThemeProvider, createTheme } from "@mui/material/styles";

const theme = createTheme({
    typography: {
        fontFamily: "var(--font-casual)",
    },
});

export default function GlobalThemeProvider({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
