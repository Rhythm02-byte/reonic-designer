import type { Metadata } from "next";
import Link from "next/link";
import { Footer, Header, Icon, Logo, pill, pillLook } from "@/components/ui";

const WIDTH = "max-w-5xl";

export const metadata: Metadata = { title: "Page not found · Home Energy Designer" };

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo />
      </Header>
      <main className={`mx-auto flex w-full flex-1 flex-col items-start justify-center gap-4 px-4 py-16 sm:px-6 ${WIDTH}`}>
        <p className="text-xs font-semibold tracking-wide text-muted uppercase">404</p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Page not found</h1>
        <p className="max-w-[65ch] text-sm">The page you&apos;re looking for doesn&apos;t exist or has moved.</p>
        <Link href="/" className={`${pill} ${pillLook.primary} mt-2`}>
          Back to the planner <Icon name="arrow" className="size-4" />
        </Link>
      </main>
      <Footer width={WIDTH}>Home Energy Designer · built for the Reonic challenge at thinc! München 2026.</Footer>
    </div>
  );
}
