"use client";
// Full-screen customer creation: name, then pick the house on the map, then land on its design screen.
import Link from "next/link"; // ours: lint fix
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Location, type GeoLocation } from "@/components/Location";
import { Button, Footer, Header, Icon, Logo, pill, pillLook } from "@/components/ui";
import { addCustomer } from "@/lib/workspace";

const WIDTH = "max-w-2xl";

export default function NewCustomerPage() {
  const router = useRouter();
  const [step, setStep] = useState<0 | 1>(0);
  const [name, setName] = useState("");
  const [location, setLocation] = useState<GeoLocation | null>(null);

  const create = () => {
    addCustomer(name.trim(), location);
    router.push("/");
  };

  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo product={false} />
      </Header>
      <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-10 sm:px-6 ${WIDTH}`}>
        <div className="space-y-4">
          <div className="space-y-1"><p className="text-xs font-medium uppercase tracking-wide text-quiet">New project · Step {step + 1} of 2</p><h1 className="text-3xl font-semibold tracking-tight text-ink">Add a customer</h1><p className="max-w-[55ch] text-sm text-quiet">Start with a name, then choose the home location. You can add the energy details in the planner.</p></div>
          <ol aria-label="Customer setup progress" className="grid grid-cols-2 gap-2">
            {["Customer details", "Home location"].map((label, index) => <li key={label} aria-current={step === index ? "step" : undefined} className={`flex items-center gap-2 border-b-2 pb-2 text-xs ${step === index ? "border-blue-600 font-medium text-ink" : step > index ? "border-zinc-400 text-quiet" : "border-zinc-200 text-quiet"}`}><span className="grid size-6 place-items-center rounded-full bg-sand tabular-nums">{step > index ? "✓" : index + 1}</span>{label}</li>)}
          </ol>
        </div>

        <AnimatePresence mode="wait" initial={false}>
        {step === 0 ? (
          <motion.div key="customer-details" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18, ease: "easeOut" }} className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6">
            <div><h2 className="text-base font-semibold text-ink">Who are we planning for?</h2><p className="mt-1 text-sm text-quiet">Use the name your team will recognize in the customer list.</p></div>
            <label className="block space-y-1 text-sm text-ink">
              <span className="font-medium">Customer name</span>
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.nativeEvent.isComposing && name.trim()) { e.preventDefault(); setStep(1); } }} // ours: Enter continues
                placeholder="e.g. Familie Meier"
                autoComplete="name"
                className="w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-blue-600 focus:outline-none"
              />
            </label>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <Link href="/" className={`${pill} ${pillLook.secondary}`}>Cancel</Link>
              <Button onClick={() => setStep(1)} disabled={!name.trim()}>Continue to location <Icon name="arrow" className="size-4" /></Button>
            </div>
          </motion.div>
        ) : (
          <motion.div key="home-location" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18, ease: "easeOut" }} className="space-y-4">
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6"><h2 className="text-base font-semibold text-ink">Where is {name.trim()}&apos;s home?</h2><p className="mt-1 text-sm text-quiet">Choose a location to help the planner understand the roof and local context. You can skip it for now.</p><div className="mt-4"><Location value={location} onChange={setLocation} /></div></div>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <Button variant="secondary" onClick={() => setStep(0)}>Back to details</Button>
              <Button onClick={create}>
                Create customer <Icon name="arrow" className="size-4" />
              </Button>
            </div>
          </motion.div>
        )}
        </AnimatePresence>
      </main>
      <Footer width={WIDTH}>
        Built for the Reonic challenge at thinc! München 2026.
      </Footer>
    </div>
  );
}
