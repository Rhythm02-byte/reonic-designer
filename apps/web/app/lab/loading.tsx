// Suspense boundary: /lab reads the run history per request (connection()), so it cannot be prerendered.
export default function Loading() {
  return <p role="status" className="mx-auto max-w-5xl px-4 py-8 text-sm text-muted sm:px-6">Loading run history…</p>;
}
