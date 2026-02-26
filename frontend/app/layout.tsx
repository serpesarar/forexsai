import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./theme.tokens.css";
import "./globals.css";
import Providers from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetBrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "ForexsAi - AI-Powered Market Analysis",
  description: "AI-powered market analysis for NASDAQ and XAUUSD - clearer trends, faster decisions.",
  manifest: "/site.webmanifest",
  metadataBase: new URL("https://www.forexsai.com"),
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
    shortcut: "/favicon.ico",
  },
  openGraph: {
    title: "ForexsAi - AI-Powered Market Analysis",
    description: "AI-powered market analysis for NASDAQ and XAUUSD - clearer trends, faster decisions.",
    url: "https://www.forexsai.com",
    siteName: "ForexsAi",
    images: [
      {
        url: "/android-chrome-512x512.png",
        width: 512,
        height: 512,
        alt: "ForexsAi Logo",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "ForexsAi - AI-Powered Market Analysis",
    description: "AI-powered market analysis for NASDAQ and XAUUSD - clearer trends, faster decisions.",
    images: ["/android-chrome-512x512.png"],
  },
  other: {
    "google-site-verification": "your-verification-code",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="premium" className={`${inter.variable} ${jetBrainsMono.variable}`}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
