# Habit Tracker — Frontend

React + Vite + TypeScript + Tailwind CSS. Mobile-first, "Soft Pastel & Inset
Card" design language. Currently runs on **mock data**; the API layer is
structured so wiring the FastAPI backend is a localized change.

## Run

```bash
npm install
npm run dev      # http://localhost:5173  (proxies /api -> http://127.0.0.1:8000)
npm run build    # -> dist/  (static bundle for nginx)
npm run preview  # serve the built bundle locally
```

## Structure

```
src/
  api/            HTTP layer. client.ts = fetch wrapper; habits.ts = endpoints
                  (mock now, real fetch calls stubbed alongside each function).
  components/     Reusable UI: ProgressRing, Toggle, PillSelector, HabitCard,
                  TopBar, BottomNav, WeekStrip.
  views/          The three archetypes + Stats/Settings:
                    Dashboard.tsx    — sticky header, week strip, habit cards,
                                       frosted bottom nav
                    HabitConfig.tsx  — inset-grouped create/edit form
                    FocusView.tsx    — full-screen gradient, progress ring, logging
  lib/            accents.ts (accent palette + tint/gradient helpers), dates.ts
  data/           mockData.ts (seed habits)
  types.ts        Domain types; API fields mirror backend Pydantic schemas,
                  frontend-only fields (emoji, accent, timeOfDay) clearly marked.
```

## Design system

Tokens live in `tailwind.config.js` (pastel surfaces, `ink` slate text scale,
per-habit `accent` palette, `rounded-card`, `shadow-card`/`shadow-inset`) and
component classes (`.card`, `.inset-group`, `.inset-row`, `.pill`, `.frosted`)
in `src/index.css`. Per-habit colors are applied as inline styles derived from
`lib/accents.ts` (Tailwind can't see dynamically composed class names).

## Wiring the real API

Each function in `src/api/habits.ts` has its real `apiFetch(...)` call commented
directly above the mock implementation. Swap them, then uncomment the
`apiFetch` import. All calls are same-origin under `/api` — Vite proxies it in
dev, nginx in prod (see `../deploy/nginx.conf`).

> Note: some UI is design-forward and not yet in the backend model —
> weekly/`x-per-week` frequency ("Day 3/5"), time-of-day, and reminders. These
> need backend fields before they can be wired.
