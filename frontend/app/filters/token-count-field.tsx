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
        <FilterOption
            name="Millions of tokens"
            help={
                "The number is millions of tokens (10 = 10 million).\n" +
                "A Cost column is inserted left of Input Cost.\n" +
                "Cost is millions × (0.90 × input $/1M + 0.10 × output $/1M) for the chosen provider.\n" +
                "The Cost range under this field keeps rows inside those dollar amounts.\n" +
                "Clearing the field hides the column and the range."
            }
        >
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
