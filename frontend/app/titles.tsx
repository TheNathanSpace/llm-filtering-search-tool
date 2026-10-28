"use client";

import { Link, Typography } from "@mui/material";
import { type CSSProperties, useLayoutEffect, useRef, useState } from "react";
import type { SxProps, Theme } from "@mui/material/styles";
import GithubLogo from "@/app/github-logo";

const railStyle: CSSProperties = {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
    height: "100%",
    gap: "0.45rem",
    margin: 0,
    paddingInline: "2.25rem",
    minWidth: 0,
    overflow: "hidden",
};

const lineStyle: CSSProperties = {
    writingMode: "sideways-lr",
    maxHeight: "100%",
    minHeight: 0,
    minWidth: 0,
    flex: "0 0 auto",
    margin: 0,
    lineHeight: 1.05,
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

/** Tagline stays smaller than the largest size that fits the rail. */
const TAGLINE_SCALE = 2 / 3;

/** Largest integer px size whose box stays inside the rail. */
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
        element.style.maxHeight = wrap ? `${maxHeight}px` : "none";
        element.style.height = wrap ? `${maxHeight}px` : "auto";
        element.style.overflow = "hidden";
    };
    while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        apply(mid);
        const rect = element.getBoundingClientRect();
        const tooTall = wrap
            ? element.scrollHeight > element.clientHeight + 1
            : rect.height > maxHeight + 1;
        const tooWide = rect.width > maxWidth + 1;
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

export default function Titles() {
    const railRef = useRef<HTMLElement>(null);
    const titleRef = useRef<HTMLHeadingElement>(null);
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
            const maxHeight = rail.clientHeight;
            const computed = getComputedStyle(rail);
            const gap = Number.parseFloat(computed.columnGap) || 0;
            const pad =
                (Number.parseFloat(computed.paddingLeft) || 0) +
                (Number.parseFloat(computed.paddingRight) || 0);
            const inner = rail.clientWidth - pad;
            if (maxHeight < 8 || inner < 8) {
                return;
            }

            const titleSize = largestFit(title, maxHeight, inner, false);
            const linkSize = largestFit(link, maxHeight, inner, false);
            const used =
                title.getBoundingClientRect().width +
                link.getBoundingClientRect().width +
                gap * 2;
            const goalFit = largestFit(
                goal,
                maxHeight,
                Math.max(8, inner - used),
                true,
            );
            const goalSize = Math.max(8, Math.round(goalFit * TAGLINE_SCALE));
            goal.style.fontSize = `${goalSize}px`;
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

    const titleFont = sizes ? `${sizes.title}px` : "13.1cqh";
    const goalFont = sizes ? `${sizes.goal}px` : "8.3cqh";
    const linkFont = sizes ? `${sizes.link}px` : "6.3cqh";

    return (
        <header ref={railRef} style={railStyle}>
            <Typography
                ref={titleRef}
                component="h1"
                variant="h1"
                style={{
                    ...lineStyle,
                    fontSize: titleFont,
                    whiteSpace: "nowrap",
                }}
                sx={textSx}
            >
                LLM rankings app
            </Typography>
            <Typography
                ref={goalRef}
                component="p"
                variant="h4"
                style={{
                    ...lineStyle,
                    fontSize: goalFont,
                    lineHeight: 1.12,
                    height: "100%",
                    whiteSpace: "normal",
                }}
                sx={textSx}
            >
                The goal is to consolidate multidimensional LLM metrics and
                benchmarks into a searchable platform.
            </Typography>
            <Link
                ref={linkRef}
                href="https://github.com/TheNathanSpace/llm-filtering-search-tool"
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
