import { Slider, Tooltip, type SliderProps } from "@mui/material";
import type { SliderValueLabelProps } from "@mui/material/Slider";

/**
 * MUI centers a 20px thumb on each end of the rail and paints a 42px hit
 * target on that thumb. Both hang outside a full-width slider and widen
 * the two-column filter panel. Inset the rail by half a thumb, and keep
 * the hit target on the thumb so it cannot stick out either.
 *
 * The hover value is a portaled tooltip. The in-slider label is wide enough
 * to grow the filter pane's horizontal overflow.
 */
function SliderHoverLabel({ children, open, value }: SliderValueLabelProps) {
    if (!children) {
        return;
    }
    const title = value == undefined || value === "" ? "" : String(value);
    return (
        <Tooltip
            open={Boolean(open) && title !== ""}
            title={title}
            placement="top"
            enterTouchDelay={0}
            disableFocusListener
            disableHoverListener
            disableTouchListener
            disableInteractive
            slotProps={{
                popper: {
                    modifiers: [
                        {
                            name: "followThumb",
                            enabled: true,
                            phase: "main",
                            effect({ instance }) {
                                let frame = 0;
                                const tick = () => {
                                    void instance.update();
                                    frame = requestAnimationFrame(tick);
                                };
                                frame = requestAnimationFrame(tick);
                                return () => {
                                    cancelAnimationFrame(frame);
                                };
                            },
                        },
                    ],
                },
            }}
        >
            {children}
        </Tooltip>
    );
}

export default function RangeSlider(properties: Readonly<SliderProps>) {
    return (
        <div style={{ paddingLeft: 10, paddingRight: 10 }}>
            <Slider
                {...properties}
                slots={{ ...properties.slots, valueLabel: SliderHoverLabel }}
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
