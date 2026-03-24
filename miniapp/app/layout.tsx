import type { Metadata, Viewport } from "next";
import Script from "next/script";
import Header from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "LongiMed",
  description: "Ethiopian Medical Consultation Platform",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#F7FAFA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body className="eth-lattice bg-surface-base min-h-screen min-h-dvh">
        <div className="relative z-10 bg-hero-mesh min-h-screen min-h-dvh">
          <Header />
          <main className="max-w-lg mx-auto px-5 pb-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
