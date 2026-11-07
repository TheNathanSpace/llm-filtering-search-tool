import { Slider, type SliderProps } from "@mui/material";

/**
 * MUI centers a 20px thumb on each end of the rail and paints a 42px hit
 * target on that thumb. Both hang outside a full-width slider and widen
 * the two-column filter panel. Inset the rail by half a thumb, and keep
 * the hit target on the thumb so it cannot stick out either.
 */
export default function RangeSlider(properties: Readonly<SliderProps>) {
    return (
        <div style={{ paddingLeft: 10, paddingRight: 10 }}>
            <Slider
                {...properties}
                sx={{
                    "& .MuiSlider-thumb::after": {
                        width: 20,
                        height: 20,
                    },
                }}
            />
        </div>
    );
}
