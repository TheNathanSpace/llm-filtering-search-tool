import { Typography } from "@mui/material";
import { toTitleCase } from "@/app/utility";
import { MuiFontCasual } from "@/app/mui-font";

interface FilterOptionParameters {
    name: string;
    children: React.ReactNode;
}

export default function FilterOption(
    parameters: Readonly<FilterOptionParameters>,
) {
    function formatName(): string {
        return `${toTitleCase(parameters.name)}:`;
    }

    return (
        <div className={"left-aligned m-4 w-full inline"}>
            <MuiFontCasual>
                <Typography variant="body1" sx={{ marginRight: "1em" }}>
                    {formatName()}
                </Typography>
            </MuiFontCasual>
            <div className="w-full">{parameters.children}</div>
        </div>
    );
}
