import type { Metadata } from "next";
import { Average_Sans, Mansalva, Sixtyfour } from "next/font/google";
import "./globals.css";
import "tailwindcss";
import AppThemeProvider from "@/app/theme-provider";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v13-appRouter";

const averageSans = Average_Sans({
    variable: "--font-average-sans",
    weight: "400",
});

const mansalva = Mansalva({
    variable: "--font-mansalva",
    weight: "400",
});

const sixtyFour = Sixtyfour({
    variable: "--font-sixtyfour",
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
            <body className="min-h-screen min-w-screen flex flex-col">
                <AppRouterCacheProvider>
                    <AppThemeProvider>{children}</AppThemeProvider>
                </AppRouterCacheProvider>
            </body>
        </html>
    );
}
