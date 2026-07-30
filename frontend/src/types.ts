// Domain types for the habit tracker frontend.
//
// The fields marked "API" mirror the FastAPI backend's Pydantic schemas so the
// mock layer can be swapped for real HTTP calls with minimal churn. Fields
// marked "frontend-only" are design/presentation concerns (emoji, accent color)
// or design-forward features not yet in the backend model (time-of-day,
// weekly frequency) — kept isolated so wiring the real API stays localized.

export type HabitType = 'build' | 'quit'
export type TrackingType = 'boolean' | 'quantity'
export type AccentColor = 'orange' | 'blue' | 'mint' | 'purple' | 'pink'

// frontend-only — not yet modeled server-side
export type TimeOfDay = 'anytime' | 'morning' | 'afternoon' | 'evening'

export interface Habit {
  // --- API (backend HabitRead) ---
  id: number
  name: string
  description: string | null
  habitType: HabitType
  trackingType: TrackingType
  targetValue: number | null
  unit: string | null
  isArchived: boolean

  // --- frontend-only presentation ---
  emoji: string
  accent: AccentColor

  // --- frontend-only, design-forward (backend deferral) ---
  timeOfDay: TimeOfDay
  reminderEnabled: boolean
}

// A habit plus today's logged progress — what the dashboard/focus views render.
export interface HabitWithProgress extends Habit {
  // For quantity habits: units done today. For boolean: 1 when done, else 0.
  progress: number
  // Target for the day. Quantity → targetValue; boolean → 1.
  goal: number
  completed: boolean
}

export interface DayCell {
  date: string // ISO yyyy-mm-dd
  label: string // e.g. "Mon"
  dayOfMonth: number
  isToday: boolean
}
