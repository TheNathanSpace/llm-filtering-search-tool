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
        <div className={"left-aligned pt-4 pl-1 pr-1 w-full"}>
            <div className="flex flex-row items-center w-full">
                <MuiFontCasual style={{ flex: "0 0 25%" }}>
                    <Typography variant="body1">{formatName()}</Typography>
                </MuiFontCasual>
                <div className="min-w-0" style={{ flex: "0 0 75%" }}>
                    {parameters.children}
                </div>
            </div>
        </div>
    );
}
