"use client";

import { ThemeProvider, createTheme, useTheme } from "@mui/material/styles";

export enum FontName {
    SANS = "sans",
    CASUAL = "casual",
    MONO = "mono",
}

interface MuiFontParameters {
    children: React.ReactNode;
    font: FontName;
    style?: React.CSSProperties;
}

export default function MuiFont(parameters: Readonly<MuiFontParameters>) {
    const parent = useTheme();
    const theme = createTheme({
        palette: {
            primary: parent.palette.primary,
        },
        typography: {
            fontFamily: `var(--font-${parameters.font.toString().toLowerCase()})`,
        },
        components: {
            // Font wrappers replace the theme. Keep hover popups and link color.
            MuiTooltip: parent.components?.MuiTooltip,
            MuiLink: parent.components?.MuiLink,
        },
    });

    return (
        <ThemeProvider theme={theme}>
            <div
                className={`font-${parameters.font.toString().toLowerCase()}!`}
                style={parameters.style ?? {}}
            >
                {parameters.children}
            </div>
        </ThemeProvider>
    );
}

interface FontChosenParameters {
    children: React.ReactNode;
    style?: React.CSSProperties;
}

export function MuiFontSans(parameters: Readonly<FontChosenParameters>) {
    return (
        <MuiFont font={FontName.SANS} style={parameters.style}>
            {parameters.children}
        </MuiFont>
    );
}

export function MuiFontCasual(parameters: Readonly<FontChosenParameters>) {
    return (
        <MuiFont font={FontName.CASUAL} style={parameters.style}>
            {parameters.children}
        </MuiFont>
    );
}

export function MuiFontMono(parameters: Readonly<FontChosenParameters>) {
    return (
        <MuiFont font={FontName.MONO} style={parameters.style}>
            {parameters.children}
        </MuiFont>
    );
}
