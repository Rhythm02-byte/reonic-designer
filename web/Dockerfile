# Web planner (Next.js). It only talks to the designer API; the address is fixed at build time (REONIC_API).
FROM node:22-slim AS build
ARG REONIC_API=http://api:8000
ENV REONIC_API=$REONIC_API NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /web
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM node:22-slim
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 REONIC_API=http://api:8000
RUN corepack enable
WORKDIR /web
COPY --from=build /web ./
USER node
EXPOSE 3000
CMD ["pnpm", "start", "-H", "0.0.0.0", "-p", "3000"]
