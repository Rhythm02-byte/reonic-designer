import type { Metadata } from "next";
import { Geist, Noto_Serif } from "next/font/google";
import "./globals.css";

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const notoSerif = Noto_Serif({ variable: "--font-noto-serif", subsets: ["latin"], style: "italic", weight: "400" });

export const metadata: Metadata = {
  title: "Home Energy Designer",
  description: "Proposes PV, battery, heat pump and wallbox designs the way an expert planner would.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geist.variable} ${notoSerif.variable} h-full antialiased`}>
      <body className="min-h-full font-sans">{children}</body>
    </html>
  );
}
