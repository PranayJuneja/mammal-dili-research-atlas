import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, IBM_Plex_Mono, Source_Sans_3 } from "next/font/google";

import "./globals.css";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const body = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "MAMMAL × DILI — Research Atlas",
    template: "%s · MAMMAL × DILI",
  },
  description:
    "A transparent research atlas for testing whether frozen MAMMAL molecular embeddings add predictive value for DILIrank 2.0 concern labels.",
  keywords: [
    "drug-induced liver injury",
    "DILIrank 2.0",
    "MAMMAL",
    "molecular embeddings",
    "scaffold validation",
  ],
  openGraph: {
    title: "MAMMAL × DILI — Research Atlas",
    description: "One question. Four matched models. A scaffold-separated answer.",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#123c56",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}

