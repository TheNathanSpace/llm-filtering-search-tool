import FilterOption from "@/app/filters/filter-option";
import { Autocomplete, Chip, TextField } from "@mui/material";
import { MuiFontSans } from "@/app/mui-font";

interface MultiSelectFilterProperties {
    name: string;
    options: string[];
    label: string;
    value?: string[];
    defaultValue?: string[];
    onChange?: (value: string[]) => void;
}

export default function MultiSelectFilter(
    properties: Readonly<MultiSelectFilterProperties>,
) {
    const { name, options, label, value, defaultValue, onChange } = properties;

    return (
        <FilterOption name={name}>
            <MuiFontSans style={{ width: "100%" }}>
                <Autocomplete
                    multiple={true}
                    options={options}
                    value={value}
                    defaultValue={defaultValue}
                    onChange={(_event, newValue) => {
                        onChange?.(newValue);
                    }}
                    disableCloseOnSelect={true}
                    renderInput={(parameters) => (
                        <TextField {...parameters} label={label} />
                    )}
                    filterSelectedOptions={true}
                    fullWidth={true}
                    renderValue={(selected, getTagProperties) =>
                        selected.map((option, index) => {
                            const { onDelete, ...other } = getTagProperties({
                                index,
                            });

                            return (
                                <Chip
                                    label={option}
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        onDelete?.(event);
                                    }}
                                    onDelete={onDelete}
                                    {...other}
                                    key={index}
                                />
                            );
                        })
                    }
                />
            </MuiFontSans>
        </FilterOption>
    );
}
