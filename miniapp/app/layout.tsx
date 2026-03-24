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
      <body className="noise bg-surface min-h-screen min-h-dvh">
        <div className="bg-mesh-teal min-h-screen min-h-dvh">
          <Header />
          <main className="max-w-lg mx-auto px-4 pb-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
