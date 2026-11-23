# WOC frontend

Next.js App Router, TypeScript, React, Tailwind CSS, Motion, Swiper, Lucide, TanStack Query, React Hook Form and Zod. Exact dependency versions are recorded in `package-lock.json`.

`npm run dev` starts development on port 4317. `npm run build` exports the site into `out/`. The parent `start-woc.ps1` serves this build with the local Django backend. See the parent README for implementation status and remaining production integrations.

Hosted deployments intentionally run as a labelled, browser-only demonstration. They do not connect to a user’s local Django server or collect payments. Generated images and reviewed Acadia-style colours are included in `public/`.
