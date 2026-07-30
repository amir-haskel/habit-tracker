import { useEffect, useState } from 'react'
import { currentTimeLabel } from '../lib/dates'

interface TopBarProps {
  filter: string
  onFilterChange: (value: string) => void
  filterOptions: string[]
}

// Sticky dashboard header: live time, filter dropdown, notification indicator.
export default function TopBar({ filter, onFilterChange, filterOptions }: TopBarProps) {
  const [time, setTime] = useState(currentTimeLabel())

  useEffect(() => {
    const id = setInterval(() => setTime(currentTimeLabel()), 30_000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="sticky top-0 z-10 frosted">
      <div className="mx-auto flex max-w-app items-center justify-between px-5 py-3">
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-bold text-ink">{time}</span>
          <span className="text-xs text-ink-faint">Today</span>
        </div>

        <div className="flex items-center gap-3">
          <label className="relative">
            <select
              value={filter}
              onChange={(e) => onFilterChange(e.target.value)}
              className="appearance-none rounded-pill bg-white py-1.5 pl-3 pr-7 text-sm font-medium text-ink-soft shadow-card focus:outline-none"
            >
              {filterOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-faint">
              ▾
            </span>
          </label>

          <button
            type="button"
            aria-label="Notifications"
            className="relative flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-card"
          >
            <span className="text-base">🔔</span>
            <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-accent-pink ring-2 ring-white" />
          </button>
        </div>
      </div>
    </header>
  )
}
