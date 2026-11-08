"use client";

import { Link, Typography } from "@mui/material";
import {
    type CSSProperties,
    type MouseEvent,
    useLayoutEffect,
    useRef,
    useState,
} from "react";
import type { SxProps, Theme } from "@mui/material/styles";
import GithubLogo from "@/app/github-logo";

const railStyle: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    justifyContent: "space-between",
    boxSizing: "border-box",
    width: "100%",
    height: "100%",
    gap: "0.75rem",
    margin: 0,
    padding: "1.25rem 1.5rem",
    minWidth: 0,
    minHeight: 0,
    overflow: "hidden",
};

const lineStyle: CSSProperties = {
    maxWidth: "100%",
    minHeight: 0,
    minWidth: 0,
    flex: "0 0 auto",
    margin: 0,
    lineHeight: 1.35,
    overflow: "hidden",
    textAlign: "left",
};

const textSx: SxProps<Theme> = {
    margin: 0,
    fontSize: "inherit",
    lineHeight: "inherit",
};

type FontSizes = {
    title: number;
    goal: number;
    link: number;
};

/** Tagline stays smaller than the largest size that fits the column. */
const TAGLINE_SCALE = 2 / 3;

/** Largest integer px size whose box stays inside the given limits. */
function largestFit(
    element: HTMLElement,
    maxHeight: number,
    maxWidth: number,
    wrap: boolean,
): number {
    let low = 8;
    let high = Math.max(low, Math.floor(maxHeight));
    let best = low;
    const apply = (size: number) => {
        element.style.fontSize = `${size}px`;
        element.style.whiteSpace = wrap ? "normal" : "nowrap";
        element.style.boxSizing = "border-box";
        element.style.width = `${maxWidth}px`;
        element.style.maxWidth = `${maxWidth}px`;
        element.style.minWidth = "0";
        element.style.maxHeight = wrap ? `${maxHeight}px` : "none";
        element.style.height = wrap ? `${maxHeight}px` : "auto";
        element.style.overflow = "hidden";
    };
    while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        apply(mid);
        const rect = element.getBoundingClientRect();
        const tooTall = wrap
            ? element.scrollHeight > element.clientHeight
            : rect.height > maxHeight;
        const tooWide = element.scrollWidth > element.clientWidth;
        if (!tooTall && !tooWide) {
            best = mid;
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    apply(best);
    return best;
}

export default function Titles({ onReset }: { onReset: () => void }) {
    const railRef = useRef<HTMLElement>(null);
    const titleRef = useRef<HTMLAnchorElement>(null);
    const goalRef = useRef<HTMLParagraphElement>(null);
    const linkRef = useRef<HTMLAnchorElement>(null);
    const [sizes, setSizes] = useState<FontSizes | null>(null);

    useLayoutEffect(() => {
        const rail = railRef.current;
        const title = titleRef.current;
        const goal = goalRef.current;
        const link = linkRef.current;
        if (!rail || !title || !goal || !link) {
            return;
        }

        const fit = () => {
            const computed = getComputedStyle(rail);
            const gap = Number.parseFloat(computed.rowGap) || 0;
            const padX =
                (Number.parseFloat(computed.paddingLeft) || 0) +
                (Number.parseFloat(computed.paddingRight) || 0);
            const padY =
                (Number.parseFloat(computed.paddingTop) || 0) +
                (Number.parseFloat(computed.paddingBottom) || 0);
            const innerWidth = rail.clientWidth - padX;
            const innerHeight = rail.clientHeight - padY;
            if (innerWidth < 8 || innerHeight < 8) {
                return;
            }

            const titleSize = largestFit(
                title,
                innerHeight * 0.42,
                innerWidth,
                true,
            );
            title.style.height = "auto";
            title.style.maxHeight = "none";
            const linkFit = largestFit(
                link,
                innerHeight * 0.22,
                innerWidth,
                false,
            );
            const linkSize = Math.min(titleSize, linkFit);
            link.style.fontSize = `${linkSize}px`;
            link.style.height = "auto";
            link.style.maxHeight = "none";
            const used =
                title.getBoundingClientRect().height +
                link.getBoundingClientRect().height +
                gap * 2;
            const goalRoom = Math.max(8, innerHeight - used);
            const goalFit = largestFit(goal, goalRoom, innerWidth, true);
            const goalSize = Math.max(8, Math.round(goalFit * TAGLINE_SCALE));
            goal.style.fontSize = `${goalSize}px`;
            goal.style.height = "auto";
            goal.style.maxHeight = "none";
            setSizes((previous) =>
                previous?.title === titleSize &&
                previous.goal === goalSize &&
                previous.link === linkSize
                    ? previous
                    : { title: titleSize, goal: goalSize, link: linkSize },
            );
        };

        fit();
        const observer = new ResizeObserver(fit);
        observer.observe(rail);
        return () => observer.disconnect();
    }, []);

    const titleFont = sizes ? `${sizes.title}px` : "2.6rem";
    const goalFont = sizes ? `${sizes.goal}px` : "1.15rem";
    const linkFont = sizes ? `${sizes.link}px` : "1.05rem";

    return (
        <header ref={railRef} style={railStyle}>
            <Typography
                ref={titleRef}
                component="a"
                href="/"
                variant="h1"
                onClick={(event: MouseEvent<HTMLAnchorElement>) => {
                    if (
                        event.button !== 0 ||
                        event.metaKey ||
                        event.ctrlKey ||
                        event.shiftKey ||
                        event.altKey
                    ) {
                        return;
                    }
                    event.preventDefault();
                    onReset();
                }}
                style={{
                    ...lineStyle,
                    fontSize: titleFont,
                    lineHeight: 1.45,
                    width: "100%",
                    whiteSpace: "normal",
                    display: "block",
                    color: "inherit",
                    textDecoration: "none",
                    cursor: "pointer",
                }}
                sx={textSx}
            >
                Tool that lets you sort and filter and analyze AI models!!
            </Typography>
            <Typography
                ref={goalRef}
                component="p"
                variant="h4"
                style={{
                    ...lineStyle,
                    fontSize: goalFont,
                    lineHeight: 1.45,
                    width: "100%",
                    whiteSpace: "normal",
                }}
                sx={textSx}
            >
                The goal is to consolidate multidimensional LLM metrics and
                benchmarks into a searchable platform.
            </Typography>
            <Link
                ref={linkRef}
                href="https://github.com/TheNathanSpace/AI-Model-Metrics"
                color="inherit"
                className="side-brand-link font-mono!"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                    ...lineStyle,
                    fontSize: linkFont,
                    display: "inline-flex",
                    alignItems: "center",
                    columnGap: "0.35em",
                    width: "max-content",
                    maxWidth: "100%",
                    whiteSpace: "nowrap",
                }}
            >
                <Typography
                    component="span"
                    variant="h6"
                    sx={textSx}
                    className="font-mono!"
                >
                    View on GitHub
                </Typography>
                <GithubLogo />
            </Link>
        </header>
    );
}
