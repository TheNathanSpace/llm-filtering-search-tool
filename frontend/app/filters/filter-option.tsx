import HelpOutlineIcon from "@mui/icons-material/HelpOutlined";
import { IconButton, Tooltip, Typography } from "@mui/material";
import { ReactNode } from "react";
import { MuiFontCasual } from "@/app/mui-font";
import { toTitleCase } from "@/app/utility";

interface FilterOptionParameters {
    name: string;
    children: React.ReactNode;
    /** Optional help shown on a circled ? after the label. */
    help?: ReactNode;
}

export default function FilterOption(
    parameters: Readonly<FilterOptionParameters>,
) {
    function formatName(): string {
        return `${toTitleCase(parameters.name)}:`;
    }

    return (
        <div className="w-full break-inside-avoid">
            <div className={"left-aligned pt-4 pl-1 pr-1 w-full"}>
                <div className="flex flex-row items-center w-full">
                    <MuiFontCasual style={{ flex: "0 0 25%", minWidth: 0 }}>
                        <div className="flex flex-row items-center gap-0.5">
                            <Typography
                                variant="body1"
                                sx={{
                                    overflowWrap: "break-word",
                                    lineHeight: 1.15,
                                }}
                            >
                                {formatName()}
                            </Typography>
                            {parameters.help !== undefined && (
                                <Tooltip
                                    title={parameters.help}
                                    enterDelay={200}
                                    slotProps={{
                                        tooltip: {
                                            sx: {
                                                maxWidth: 320,
                                                whiteSpace: "pre-line",
                                            },
                                        },
                                    }}
                                >
                                    <IconButton
                                        size="small"
                                        aria-label={`${toTitleCase(parameters.name)} search help`}
                                        sx={{ p: 0.25 }}
                                    >
                                        <HelpOutlineIcon
                                            sx={{ fontSize: 16 }}
                                        />
                                    </IconButton>
                                </Tooltip>
                            )}
                        </div>
                    </MuiFontCasual>
                    <div className="min-w-0" style={{ flex: "0 0 75%" }}>
                        {parameters.children}
                    </div>
                </div>
            </div>
        </div>
    );
}
