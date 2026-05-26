import type { Metadata } from "next";
import { Average_Sans, Mansalva, Sixtyfour } from "next/font/google";
import "./globals.css";
import "tailwindcss";

const averageSans = Average_Sans({
    variable: "--font-sans",
    weight: "400",
});

const mansalva = Mansalva({
    variable: "--font-casual",
    weight: "400",
});

const sixtyFour = Sixtyfour({
    variable: "--font-mono",
});

export const metadata: Metadata = {
    title: "LLM Rankings",
    description:
        " The goal is to consolidate multidimensional LLM metrics and benchmarks into a searchable platform.",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html
            lang="en"
            className={`${mansalva.variable} ${averageSans.variable} ${sixtyFour.variable} h-full antialiased`}
        >
            <body className="min-h-full flex flex-col">{children}</body>
        </html>
    );
}
