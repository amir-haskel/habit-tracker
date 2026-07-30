import { Link } from 'react-router-dom'
import type { HabitWithProgress } from '../types'
import { accentHex, tint } from '../lib/accents'

function formatProgress(habit: HabitWithProgress): string {
  if (habit.trackingType === 'boolean') {
    return habit.completed ? 'Done today' : habit.habitType === 'quit' ? 'Stay strong' : 'Not yet'
  }
  const unit = habit.unit ? ` ${habit.unit}` : ''
  return `${habit.progress} / ${habit.goal}${unit}`
}

// Dashboard habit card — soft tinted background, emoji, progress + completion.
export default function HabitCard({ habit }: { habit: HabitWithProgress }) {
  const ratio = habit.goal > 0 ? habit.progress / habit.goal : 0
  const accent = accentHex[habit.accent]

  return (
    <Link
      to={`/habit/${habit.id}`}
      className="block rounded-card p-4 shadow-card transition-shadow hover:shadow-card-hover"
      style={{ backgroundColor: tint(habit.accent, 0.14) }}
    >
      <div className="flex items-center gap-3.5">
        <div
          className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl text-2xl"
          style={{ backgroundColor: tint(habit.accent, 0.25) }}
        >
          {habit.emoji}
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-ink">{habit.name}</p>
          <p className="text-sm font-medium" style={{ color: accent }}>
            {formatProgress(habit)}
          </p>
        </div>

        {habit.completed ? (
          <div
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-white"
            style={{ backgroundColor: accent }}
          >
            ✓
          </div>
        ) : (
          <span className="flex-shrink-0 text-ink-faint">›</span>
        )}
      </div>

      {habit.trackingType === 'quantity' && (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-pill bg-white/60">
          <div
            className="h-full rounded-pill transition-all"
            style={{ width: `${Math.min(100, ratio * 100)}%`, backgroundColor: accent }}
          />
        </div>
      )}
    </Link>
  )
}
