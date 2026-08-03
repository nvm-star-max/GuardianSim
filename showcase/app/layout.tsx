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
      "Think thousands. Execute one. One AMD Radeon GPU runs 16,384 parallel robot worlds across a 293.6-million-step frozen endurance suite, then demonstrates a separate 4,608-to-1 formal decision run.",
    icons: {
      icon: "/favicon.svg",
      shortcut: "/favicon.svg",
    },
    openGraph: {
      title: "GuardianSim: Parallel Futures",
      description:
        "One Radeon GPU. 16,384 full robot worlds. 278,051 environment steps per second P50. See parallel ROCm physics become one robot decision.",
      type: "website",
    },
    twitter: {
      card: "summary",
      title: "GuardianSim: Parallel Futures",
      description:
        "Think thousands. Execute one. Radeon runs 16,384 robot worlds at 98.33% average GPU use, then turns a separate 4,608-pair workload into one robot action.",
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
