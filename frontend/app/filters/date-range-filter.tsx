import FilterOption from "@/app/filters/filter-option";
import { Slider, Typography } from "@mui/material";
import { MuiFontSans } from "@/app/mui-font";
import dayjs, { Dayjs } from "dayjs";
import { useState } from "react";

/**
 * Props for the DateRangeFilter component.
 *
 * - `name`: The label displayed next to the filter.
 * - `minDate`: The earliest selectable date.
 * - `maxDate`: The latest selectable date.
 * - `defaultStart` / `defaultEnd`: Optional initial range. If omitted the range defaults to the full span.
 * - `onChange`: Callback invoked when the user changes the range. Receives a tuple of Dayjs objects.
 */
interface DateRangeFilterProperties {
    name: string;
    minDate: Dayjs;
    maxDate: Dayjs;
    defaultStart?: Dayjs;
    defaultEnd?: Dayjs;
    onChange?: (range: [Dayjs, Dayjs]) => void;
}

/**
 * A date range picker built on top of MUI's Slider component. The slider works with
 * numeric timestamps (milliseconds since epoch) and formats the tooltip values
 * using dayjs for a human‑readable date string.
 */
export default function DateRangeFilter(
    properties: Readonly<DateRangeFilterProperties>,
) {
    const { name, minDate, maxDate, defaultStart, defaultEnd, onChange } =
        properties;

    // Convert dates to numeric values for the slider (ms). Use a step of one day.
    const min = minDate.valueOf();
    const max = maxDate.valueOf();
    const step = 24 * 60 * 60 * 1000; // one day in ms

    const initialStart = defaultStart?.valueOf() ?? min;
    const initialEnd = defaultEnd?.valueOf() ?? max;

    const [value, setValue] = useState<number[]>([initialStart, initialEnd]);

    const handleChange = (event: Event, newValue: number | number[]) => {
        const numeric = newValue as number[];
        setValue(numeric);
        if (onChange) {
            onChange([dayjs(numeric[0]), dayjs(numeric[1])]);
        }
    };

    // Format the value label shown on the slider thumb.
    const valueLabelFormat = (value: number) =>
        dayjs(value).format("MMM D, YYYY");

    return (
        <FilterOption name={name}>
            <MuiFontSans>
                <Slider
                    value={value}
                    onChange={handleChange}
                    valueLabelDisplay="auto"
                    valueLabelFormat={valueLabelFormat}
                    min={min}
                    max={max}
                    step={step}
                />
                {/* Show selected range in a readable format underneath the slider */}
                <Typography
                    variant="body2"
                    sx={{ mt: -1, textAlign: "center", lineHeight: 1.2 }}
                >
                    {dayjs(value[0]).format("MMM D, YYYY")} –{" "}
                    {dayjs(value[1]).format("MMM D, YYYY")}
                </Typography>
            </MuiFontSans>
        </FilterOption>
    );
}
