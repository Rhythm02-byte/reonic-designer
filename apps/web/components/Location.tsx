"use client";
// Address -> draggable pin on a satellite map -> real roof data from Google's Solar API.
// A sanity check next to the model's proposal, not an input to it (the trained model takes
// household/consumption data, not roof geometry; wiring this into it would mean retraining).
import { importLibrary, setOptions } from "@googlemaps/js-api-loader";
import { useEffect, useId, useRef, useState } from "react";
import { num } from "@/lib/copy";
import { fetchRoof, type RoofInfo } from "@/lib/roof";
import { Card, ErrorNote, Icon, Skeleton, Spinner } from "./ui";

export type GeoLocation = { address: string; lat: number; lng: number };
type SolarInfo = RoofInfo;

const DEFAULT_CENTER = { lat: 48.1351, lng: 11.582 }; // Munich: thinc! München 2026

// setOptions() may only run once; React StrictMode double-invokes effects in dev.
let optionsSet = false;

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api/${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body), signal: AbortSignal.timeout(20_000) });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error ?? `Request failed (${res.status})`);
  return data as T;
}

export function Location({ value, onChange }: { value: GeoLocation | null; onChange: (v: GeoLocation | null) => void }) {
  const addressId = useId();
  const mapDiv = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const requestId = useRef(0);
  const solarId = useRef(0);
  const [addressText, setAddressText] = useState(value?.address ?? "");
  const [solar, setSolar] = useState<SolarInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [mapReady, setMapReady] = useState(false);
  const [solarLoading, setSolarLoading] = useState(false);

  // Load the map once; a missing/placeholder key fails here with a message instead of a blank div.
  useEffect(() => {
    let cancelled = false;
    let cleanupMap: (() => void) | undefined;
    const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!key) return; // ours: lint fix, the message is derived below instead of set in the effect
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
      // OverlayView provides the exact geographic position under a held pointer.
      const projection = new google.maps.OverlayView();
      projection.onAdd = () => {};
      projection.draw = () => {};
      projection.onRemove = () => {};
      projection.setMap(map);
      const element = mapDiv.current;
      let hold: ReturnType<typeof setTimeout> | undefined;
      let origin: { x: number; y: number; pointerId: number } | null = null;
      const cancelHold = () => { clearTimeout(hold); hold = undefined; origin = null; };
      const pointerDown = (event: PointerEvent) => {
        if (!event.isPrimary || event.button !== 0 || (event.target instanceof Element && event.target.closest("button, a, input, [role=button]"))) return;
        cancelHold();
        origin = { x: event.clientX, y: event.clientY, pointerId: event.pointerId };
        const { clientX, clientY } = event;
        hold = setTimeout(() => {
          const rect = element.getBoundingClientRect();
          const point = new google.maps.Point(clientX - rect.left, clientY - rect.top);
          const position = projection.getProjection()?.fromContainerPixelToLatLng(point);
          cancelHold();
          if (position) void placeAt(position.lat(), position.lng(), true);
        }, 650);
      };
      const pointerMove = (event: PointerEvent) => {
        if (origin && event.pointerId === origin.pointerId && Math.hypot(event.clientX - origin.x, event.clientY - origin.y) > 10) cancelHold();
      };
      const pointerEnd = (event: PointerEvent) => { if (origin?.pointerId === event.pointerId) cancelHold(); };
      element.addEventListener("pointerdown", pointerDown, true);
      window.addEventListener("pointermove", pointerMove, true);
      window.addEventListener("pointerup", pointerEnd, true);
      window.addEventListener("pointercancel", pointerEnd, true);
      cleanupMap = () => {
        cancelHold();
        element.removeEventListener("pointerdown", pointerDown, true);
        window.removeEventListener("pointermove", pointerMove, true);
        window.removeEventListener("pointerup", pointerEnd, true);
        window.removeEventListener("pointercancel", pointerEnd, true);
        projection.setMap(null);
        google.maps.event.clearInstanceListeners(marker);
        marker.setMap(null);
      };
      marker.addListener("dragend", () => {
        const pos = marker.getPosition();
        if (pos) placeAt(pos.lat(), pos.lng(), true);
      });
      mapRef.current = map;
      markerRef.current = marker;
      setMapReady(true);
      if (value) fetchSolar(value.lat, value.lng);
    }, (e: Error) => setError(e.message));
    return () => {
      cancelled = true;
      cleanupMap?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once; later moves go through placeAt/markerRef.
  }, []);

  async function fetchSolar(lat: number, lng: number) {
    const id = ++solarId.current;
    setSolarLoading(true);
    try {
      const info = await fetchRoof(lat, lng);
      if (id === solarId.current) setSolar(info);
    } catch (e) {
      if (id === solarId.current) {
        setSolar(null);
        setError((e as Error).message);
      }
    } finally {
      if (id === solarId.current) setSolarLoading(false);
    }
  }

  // The one place that moves the pin, whichever side triggered it (typed address or drag).
  async function placeAt(lat: number, lng: number, fromDrag: boolean) {
    const id = ++requestId.current;
    solarId.current++;
    setError(null);
    markerRef.current?.setPosition({ lat, lng });
    mapRef.current?.panTo({ lat, lng });
    try {
      const address = fromDrag ? (await postJson<{ formatted_address: string }>("geocode", { lat, lng })).formatted_address : addressText.trim();
      if (id !== requestId.current) return;
      setAddressText(address);
      onChange({ address, lat, lng });
      fetchSolar(lat, lng);
    } catch (e) {
      if (id === requestId.current) setError((e as Error).message);
    }
  }

  // Debounced forward geocode as the planner types an address.
  useEffect(() => {
    const trimmed = addressText.trim();
    if (!trimmed || trimmed === value?.address) return;
    const id = requestId.current;
    const t = setTimeout(() => {
      setLoading(true); // ours: lint fix (not synchronously in the effect)
      postJson<{ lat: number; lng: number; formatted_address: string }>("geocode", { address: trimmed })
        .then((r) => {
          if (id !== requestId.current) return;
          onChange({ address: r.formatted_address, lat: r.lat, lng: r.lng });
          markerRef.current?.setPosition({ lat: r.lat, lng: r.lng });
          mapRef.current?.panTo({ lat: r.lat, lng: r.lng });
          fetchSolar(r.lat, r.lng);
          setError(null);
        }, (e: Error) => { if (id === requestId.current) setError(e.message); })
        .finally(() => { if (id === requestId.current) setLoading(false); });
    }, 600);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only the typed text should re-trigger this.
  }, [addressText]);

  return (
    <Card className="space-y-3 p-4">
      <div className="flex items-center gap-2 text-sm text-ink">
        <Icon name="pin" />
        <label htmlFor={addressId} className="font-medium">Location</label>
      </div>
      <input
        id={addressId}
        type="text"
        placeholder="Enter the address"
        value={addressText}
        onChange={(e) => {
          requestId.current++; solarId.current++; setLoading(false); setSolar(null);
          setAddressText(e.target.value);
          if (!e.target.value.trim()) onChange(null);
        }}
        className="w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-blue-600 focus:outline-none"
      />
      <div className="relative h-56 w-full">
        <div ref={mapDiv} className="h-56 w-full rounded-xl bg-sand" />
        {!mapReady && process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY && <Skeleton className="absolute inset-0 rounded-xl" />}
      </div>
      <p className="text-xs text-muted">Drag the pin or press and hold a spot on the map to place it.</p>
      <ErrorNote error={error} />
      {!process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY && <p className="text-xs text-quiet">Map preview is off: no Google Maps key is set on this machine.</p>} {/* ours: not an error */}
      {loading && (
        <p className="flex items-center gap-1.5 text-xs text-quiet">
          <Spinner className="size-3.5 text-ink/40" />
          Looking up the address…
        </p>
      )}
      {solarLoading ? <Skeleton className="h-14" /> : solar && <SolarFacts solar={solar} />}
    </Card>
  );
}

function SolarFacts({ solar }: { solar: SolarInfo }) {
  if (!solar.covered) {
    return <p className="text-xs text-quiet">No Google Solar roof data for this address.</p>;
  }
  const kwp = solar.maxArrayPanelsCount && solar.panelCapacityWatts ? (solar.maxArrayPanelsCount * solar.panelCapacityWatts) / 1000 : null;
  return (
    <dl className="grid grid-cols-3 gap-2 border-t border-zinc-200 pt-3 text-center">
      <div>
        <dt className="text-xs text-muted">Roof potential</dt>
        <dd className="text-sm font-semibold tabular-nums text-ink">{kwp ? `${num(kwp)} kWp` : "n/a"}</dd>
      </div>
      <div>
        <dt className="text-xs text-muted">Max. panels</dt>
        <dd className="text-sm font-semibold tabular-nums text-ink">{solar.maxArrayPanelsCount ?? "n/a"}</dd>
      </div>
      <div>
        <dt className="text-xs text-muted">Sun hours / year</dt>
        <dd className="text-sm font-semibold tabular-nums text-ink">{solar.maxSunshineHoursPerYear ? num(solar.maxSunshineHoursPerYear, 0) : "n/a"}</dd>
      </div>
    </dl>
  );
}
