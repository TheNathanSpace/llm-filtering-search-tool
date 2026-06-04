import { ThemeProvider, createTheme } from "@mui/material/styles";

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
    const theme = createTheme({
        typography: {
            fontFamily: `var(--font-${parameters.font.toString().toLowerCase()})`,
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
