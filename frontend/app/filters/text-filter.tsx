import FilterOption from "@/app/filters/filter-option";
import { MuiFontSans } from "@/app/mui-font";
import { TextField } from "@mui/material";
import { ReactNode } from "react";

interface TextFilterProperties {
    name: string;
    label: string;
    value: string;
    onChange?: (value: string) => void;
    help?: ReactNode;
}

export default function TextFilter(
    properties: Readonly<TextFilterProperties>,
) {
    const { name, label, value, onChange, help } = properties;

    return (
        <FilterOption name={name} help={help}>
            <MuiFontSans style={{ width: "100%" }}>
                <TextField
                    label={label}
                    value={value}
                    onChange={(event) => {
                        onChange?.(event.target.value);
                    }}
                    fullWidth={true}
                    size="small"
                />
            </MuiFontSans>
        </FilterOption>
    );
}
