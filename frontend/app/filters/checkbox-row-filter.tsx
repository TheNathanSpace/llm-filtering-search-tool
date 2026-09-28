import FilterOption from "@/app/filters/filter-option";
import { toTitleCase } from "@/app/utility";
import { MuiFontSans } from "@/app/mui-font";
import {
    Checkbox,
    FormControlLabel,
    FormGroup,
    Typography,
} from "@mui/material";

interface CheckboxRowFilterProperties<T extends string> {
    name: string;
    options: readonly T[];
    value: readonly T[];
    onChange: (value: T[]) => void;
}

export default function CheckboxRowFilter<T extends string>(
    properties: Readonly<CheckboxRowFilterProperties<T>>,
) {
    const { name, options, value, onChange } = properties;
    const selected = new Set(value);

    return (
        <FilterOption name={name}>
            <MuiFontSans>
                <FormGroup
                    row={true}
                    role="group"
                    aria-label={name}
                    sx={{
                        flexWrap: "wrap",
                        columnGap: 1,
                        rowGap: 0.5,
                    }}
                >
                    {options.map((option) => (
                        <FormControlLabel
                            key={option}
                            labelPlacement="bottom"
                            sx={{
                                margin: 0,
                                minWidth: 72,
                            }}
                            control={
                                <Checkbox
                                    size="small"
                                    checked={selected.has(option)}
                                    onChange={(event) => {
                                        const next = new Set(selected);
                                        if (event.target.checked) {
                                            next.add(option);
                                        } else {
                                            next.delete(option);
                                        }
                                        onChange(
                                            options.filter((item) =>
                                                next.has(item),
                                            ),
                                        );
                                    }}
                                />
                            }
                            label={
                                <Typography
                                    variant="caption"
                                    sx={{ textAlign: "center" }}
                                >
                                    {toTitleCase(option)}
                                </Typography>
                            }
                        />
                    ))}
                </FormGroup>
            </MuiFontSans>
        </FilterOption>
    );
}
