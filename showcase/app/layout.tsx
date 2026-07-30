import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host") ?? "localhost";
  const protocol = host.startsWith("localhost") ? "http" : "https";
  const metadataBase = new URL(`${protocol}://${host}`);

  return {
    metadataBase,
    title: "GuardianSim: Parallel Futures",
    description:
      "4,608 physical counterfactuals. One action. An evidence-backed parallel Physical AI decision system on AMD Radeon.",
    icons: {
      icon: "/favicon.svg",
      shortcut: "/favicon.svg",
    },
    openGraph: {
      title: "GuardianSim: Parallel Futures",
      description:
        "18 actions face 256 uncertainty worlds each on AMD Radeon. Explore the verified 4,608-pair run and try to break GuardianSim.",
      type: "website",
    },
    twitter: {
      card: "summary",
      title: "GuardianSim: Parallel Futures",
      description:
        "Radeon parallel physics turns 4,608 bounded robot futures into an explainable execute-or-stop decision.",
    },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
