import type { NextConfig } from "next";

// The engine (services/engine, uvicorn on :8000). The browser only talks to Next, which proxies /engine/* to it,
// so there is no CORS to configure. Override with ENGINE_URL or NEXT_PUBLIC_ENGINE_URL.
const ENGINE = process.env.ENGINE_URL ?? process.env.NEXT_PUBLIC_ENGINE_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/engine/:path*", destination: `${ENGINE}/:path*` }];
  },
};

export default nextConfig;
