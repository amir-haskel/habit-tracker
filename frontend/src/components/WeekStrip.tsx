import { currentWeek } from '../lib/dates'

// Horizontally scrollable week calendar — 7 circular day bubbles.
export default function WeekStrip() {
  const week = currentWeek()

  return (
    <div className="no-scrollbar flex gap-3 overflow-x-auto pb-1">
      {week.map((day) => (
        <div key={day.date} className="flex flex-shrink-0 flex-col items-center gap-1.5">
          <span className="text-xs font-medium text-ink-faint">{day.label}</span>
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-full text-sm font-semibold transition-colors ${
              day.isToday ? 'bg-ink text-white shadow-card' : 'bg-white text-ink-soft'
            }`}
          >
            {day.dayOfMonth}
          </div>
        </div>
      ))}
    </div>
  )
}
