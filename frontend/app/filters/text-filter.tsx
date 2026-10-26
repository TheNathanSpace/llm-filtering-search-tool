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
    /** One-line textarea the user can drag taller. */
    resizable?: boolean;
}

export default function TextFilter(properties: Readonly<TextFilterProperties>) {
    const {
        name,
        label,
        value,
        onChange,
        help,
        resizable = false,
    } = properties;

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
                    multiline={resizable}
                    minRows={resizable ? 1 : undefined}
                    slotProps={
                        resizable
                            ? {
                                  input: { inputComponent: "textarea" },
                                  htmlInput: {
                                      rows: 1,
                                      style: { resize: "vertical" },
                                  },
                              }
                            : undefined
                    }
                />
            </MuiFontSans>
        </FilterOption>
    );
}
