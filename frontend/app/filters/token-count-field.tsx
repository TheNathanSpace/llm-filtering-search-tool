import FilterOption from "@/app/filters/filter-option";
import { MuiFontSans } from "@/app/mui-font";
import { TextField } from "@mui/material";

interface TokenCountFieldProperties {
    value: string;
    onChange: (value: string) => void;
}

export default function TokenCountField(
    properties: Readonly<TokenCountFieldProperties>,
) {
    const { value, onChange } = properties;

    return (
        <FilterOption name="Millions of tokens">
            <MuiFontSans>
                <TextField
                    value={value}
                    onChange={(event) => {
                        onChange(event.target.value);
                    }}
                    placeholder="e.g. 10"
                    size="small"
                    type="number"
                    sx={{ width: "8rem" }}
                    slotProps={{
                        htmlInput: {
                            min: 0,
                            step: "any",
                            "aria-label": "Token count in millions",
                        },
                    }}
                />
            </MuiFontSans>
        </FilterOption>
    );
}
