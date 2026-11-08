"use client";
// Address -> draggable pin on a satellite map -> real roof data from Google's Solar API.
// A sanity check next to the model's proposal, not an input to it (the trained model takes
// household/consumption data, not roof geometry; wiring this into it would mean retraining).
import { importLibrary, setOptions } from "@googlemaps/js-api-loader";
import { useEffect, useId, useRef, useState } from "react";
import { num } from "@/lib/copy";
import { Card, ErrorNote, Icon } from "./ui";

export type GeoLocation = { address: string; lat: number; lng: number };
type SolarInfo =
  | { covered: true; maxArrayPanelsCount: number | null; maxArrayAreaMeters2: number | null; maxSunshineHoursPerYear: number | null; panelCapacityWatts: number | null }
  | { covered: false };

const DEFAULT_CENTER = { lat: 48.1351, lng: 11.582 }; // Munich: thinc! München 2026

// setOptions() may only run once; React StrictMode double-invokes effects in dev.
let optionsSet = false;

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api/${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error ?? `Request failed (${res.status})`);
  return data as T;
}

export function Location({ value, onChange }: { value: GeoLocation | null; onChange: (v: GeoLocation | null) => void }) {
  const addressId = useId();
  const mapDiv = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const [addressText, setAddressText] = useState(value?.address ?? "");
  const [solar, setSolar] = useState<SolarInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Load the map once; a missing/placeholder key fails here with a message instead of a blank div.
  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!key) return; // ours: lint fix, the message is derived below instead of set in the effect
    let cancelled = false;
    if (!optionsSet) {
      setOptions({ key });
      optionsSet = true;
    }
    importLibrary("maps").then((lib) => {
      const { Map } = lib as google.maps.MapsLibrary;
      if (cancelled || !mapDiv.current) return;
      const center = value ?? DEFAULT_CENTER;
      const map = new Map(mapDiv.current, { center, zoom: 19, mapTypeId: "satellite", streetViewControl: false, fullscreenControl: false });
      const marker = new google.maps.Marker({ map, position: center, draggable: true });
      marker.addListener("dragend", () => {
        const pos = marker.getPosition();
        if (pos) placeAt(pos.lat(), pos.lng(), true);
      });
      mapRef.current = map;
      markerRef.current = marker;
      if (value) fetchSolar(value.lat, value.lng);
    }, (e: Error) => setError(e.message));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once; later moves go through placeAt/markerRef.
  }, []);

  async function fetchSolar(lat: number, lng: number) {
    try {
      setSolar(await postJson<SolarInfo>("solar", { lat, lng }));
    } catch (e) {
      setSolar(null);
      setError((e as Error).message);
    }
  }

  // The one place that moves the pin, whichever side triggered it (typed address or drag).
  async function placeAt(lat: number, lng: number, fromDrag: boolean) {
    setError(null);
    markerRef.current?.setPosition({ lat, lng });
    mapRef.current?.panTo({ lat, lng });
    try {
      const address = fromDrag ? (await postJson<{ formatted_address: string }>("geocode", { lat, lng })).formatted_address : addressText.trim();
      setAddressText(address);
      onChange({ address, lat, lng });
      fetchSolar(lat, lng);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  // Debounced forward geocode as the planner types an address.
  useEffect(() => {
    const trimmed = addressText.trim();
    if (!trimmed || trimmed === value?.address) return;
    const t = setTimeout(() => {
      setLoading(true); // ours: lint fix (not synchronously in the effect)
      postJson<{ lat: number; lng: number; formatted_address: string }>("geocode", { address: trimmed })
        .then((r) => {
          onChange({ address: r.formatted_address, lat: r.lat, lng: r.lng });
          markerRef.current?.setPosition({ lat: r.lat, lng: r.lng });
          mapRef.current?.panTo({ lat: r.lat, lng: r.lng });
          fetchSolar(r.lat, r.lng);
          setError(null);
        }, (e: Error) => setError(e.message))
        .finally(() => setLoading(false));
    }, 600);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only the typed text should re-trigger this.
  }, [addressText]);

  return (
    <Card className="space-y-3 p-4">
      <div className="flex items-center gap-2 text-sm text-ink">
        <Icon name="pin" />
        <label htmlFor={addressId} className="font-medium">Standort</label>
      </div>
      <input
        id={addressId}
        type="text"
        placeholder="Adresse eingeben"
        value={addressText}
        onChange={(e) => setAddressText(e.target.value)}
        className="w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-blue-600 focus:outline-none"
      />
      <div ref={mapDiv} className="h-56 w-full rounded-xl bg-sand" />
      <p className="text-xs text-muted">Pin ziehen, um die Dachkante genau zu treffen.</p>
      <ErrorNote error={error ?? (process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ? null : "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is not set")} />
      {loading && <p className="text-xs text-quiet">Adresse wird gesucht…</p>}
      {solar && <SolarFacts solar={solar} />}
    </Card>
  );
}

function SolarFacts({ solar }: { solar: SolarInfo }) {
  if (!solar.covered) {
    return <p className="text-xs text-quiet">Für diese Adresse liegen keine Google-Solar-Dachdaten vor.</p>;
  }
  const kwp = solar.maxArrayPanelsCount && solar.panelCapacityWatts ? (solar.maxArrayPanelsCount * solar.panelCapacityWatts) / 1000 : null;
  return (
    <dl className="grid grid-cols-3 gap-2 border-t border-zinc-200 pt-3 text-center">
      <div>
        <dt className="text-xs text-muted">Dach-Potenzial</dt>
        <dd className="text-sm font-semibold tabular-nums text-ink">{kwp ? `${num(kwp)} kWp` : "n/a"}</dd>
      </div>
      <div>
        <dt className="text-xs text-muted">Max. Module</dt>
        <dd className="text-sm font-semibold tabular-nums text-ink">{solar.maxArrayPanelsCount ?? "n/a"}</dd>
      </div>
      <div>
        <dt className="text-xs text-muted">Sonnenstunden/Jahr</dt>
        <dd className="text-sm font-semibold tabular-nums text-ink">{solar.maxSunshineHoursPerYear ? num(solar.maxSunshineHoursPerYear, 0) : "n/a"}</dd>
      </div>
    </dl>
  );
}
