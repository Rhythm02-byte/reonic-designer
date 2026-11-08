import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import HiddenMenu from "@/components/HiddenMenu"; // ours:

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Home Energy Designer",
  description: "Proposes PV, battery, heat pump and wallbox designs the way an expert planner would.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geist.variable} h-full antialiased`}>
      <body className="min-h-full font-sans">
        {children}
        <HiddenMenu /> {/* ours: triple-tap the logo for pitch mode / lab results */}
      </body>
    </html>
  );
}
