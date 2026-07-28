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
      "See three futures before the robot moves. An interactive, evidence-backed safety time machine for Physical AI on AMD Radeon.",
    icons: {
      icon: "/favicon.svg",
      shortcut: "/favicon.svg",
    },
    openGraph: {
      title: "GuardianSim: Parallel Futures",
      description:
        "See three futures before the robot moves. Try to break GuardianSim in a verified counterfactual safety arena.",
      type: "website",
      images: [
        { url: "/og-parallel-futures.png", width: 1200, height: 630 },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: "GuardianSim: Parallel Futures",
      description:
        "An interactive counterfactual safety time machine for robot manipulation on AMD Radeon.",
      images: ["/og-parallel-futures.png"],
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
