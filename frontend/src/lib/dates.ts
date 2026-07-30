import type { DayCell } from '../types'

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

// The current week, Monday-first, as 7 day cells for the calendar strip.
export function currentWeek(today = new Date()): DayCell[] {
  const monday = new Date(today)
  const offset = (today.getDay() + 6) % 7 // days since Monday
  monday.setDate(today.getDate() - offset)

  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return {
      date: d.toISOString().slice(0, 10),
      label: DAY_LABELS[d.getDay()],
      dayOfMonth: d.getDate(),
      isToday: d.toDateString() === today.toDateString(),
    }
  })
}

export function currentTimeLabel(now = new Date()): string {
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
