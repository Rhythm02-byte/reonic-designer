"use client";
// Full-screen customer creation: name, then pick the house on the map, then land on its design screen.
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { Location, type GeoLocation } from "@/components/Location";
import { Button, Footer, Header, Icon, Logo, pill, pillLook } from "@/components/ui";
import { addCustomer, TEAM, useWorkspace } from "@/lib/workspace";

const WIDTH = "max-w-2xl";
const selectClass = "w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 focus:ring-2 focus:ring-blue-600 focus:outline-none";

export default function NewCustomerPage() {
  const router = useRouter();
  const ws = useWorkspace();
  const [step, setStep] = useState<0 | 1>(0);
  const [name, setName] = useState("");
  const [owner, setOwner] = useState(ws.me);
  const [location, setLocation] = useState<GeoLocation | null>(null);

  const create = () => {
    addCustomer(name.trim(), location, owner);
    router.push("/");
  };

  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo product={false} />
      </Header>
      <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-10 sm:px-6 ${WIDTH}`}>
        <div className="space-y-1">
          <p className="text-xs text-quiet">Step {step + 1} of 2</p>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">New customer</h1>
        </div>

        {step === 0 ? (
          <div className="space-y-4 rounded-2xl border border-zinc-200 bg-white p-5">
            <label className="block space-y-1 text-sm text-ink">
              <span className="font-medium">Customer name</span>
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.nativeEvent.isComposing && name.trim()) { e.preventDefault(); setStep(1); } }} // ours: Enter continues
                placeholder="e.g. Familie Meier"
                className="w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-blue-600 focus:outline-none"
              />
            </label>
            <label className="block space-y-1 text-sm text-ink">
              <span className="font-medium">Owner</span>
              <select value={owner} onChange={(e) => setOwner(e.target.value)} className={selectClass}>
                {TEAM.map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </label>
            <div className="flex gap-2">
              <Link href="/" className={`${pill} ${pillLook.secondary}`}>Cancel</Link>
              <Button onClick={() => setStep(1)} disabled={!name.trim()}>Next: pick house</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <Location value={location} onChange={setLocation} />
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setStep(0)}>Back</Button>
              <Button onClick={create}>
                Create customer <Icon name="arrow" className="size-4" />
              </Button>
            </div>
          </div>
        )}
      </main>
      <Footer width={WIDTH}>
        Built for the Reonic challenge at thinc! München 2026.
      </Footer>
    </div>
  );
}
