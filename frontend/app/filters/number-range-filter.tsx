import FilterOption from "@/app/filters/filter-option";
import { Slider, Typography } from "@mui/material";
import { MuiFontSans } from "@/app/mui-font";
import { useState } from "react";
import { formatNumber } from "@/app/utility";

interface NumberRangeFilterProperties {
    name: string;
    minValue: number;
    maxValue: number;
    defaultStart?: number;
    defaultEnd?: number;
    onChange?: (range: [number, number]) => void;
    step?: number;
}

export default function NumberRangeFilter(
    properties: Readonly<NumberRangeFilterProperties>,
) {
    const initialStart = properties.defaultStart ?? properties.minValue;
    const initialEnd = properties.defaultEnd ?? properties.maxValue;

    const [value, setValue] = useState<number[]>([initialStart, initialEnd]);

    const handleChange = (event: Event, newValue: number | number[]) => {
        const numeric = newValue as number[];
        setValue(numeric);
        if (properties.onChange) {
            properties.onChange([numeric[0], numeric[1]]);
        }
    };

    return (
        <FilterOption name={properties.name}>
            <MuiFontSans>
                <Slider
                    value={value}
                    onChange={handleChange}
                    valueLabelDisplay="auto"
                    valueLabelFormat={formatNumber}
                    min={properties.minValue}
                    max={properties.maxValue}
                    step={properties.step ?? 100}
                />
                {/* Show selected range in a readable format underneath the slider */}
                <Typography
                    variant="body2"
                    sx={{ mt: -1, textAlign: "center", lineHeight: 1.2 }}
                >
                    {formatNumber(value[0])} – {formatNumber(value[1])}
                </Typography>
            </MuiFontSans>
        </FilterOption>
    );
}
