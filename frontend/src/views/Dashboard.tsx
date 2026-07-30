import { useEffect, useMemo, useState } from 'react'
import TopBar from '../components/TopBar'
import WeekStrip from '../components/WeekStrip'
import BottomNav from '../components/BottomNav'
import HabitCard from '../components/HabitCard'
import { listHabits } from '../api/habits'
import type { HabitWithProgress } from '../types'

const FILTERS = ['All', 'Morning', 'Afternoon', 'Evening', 'Anytime']

export default function Dashboard() {
  const [habits, setHabits] = useState<HabitWithProgress[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')

  useEffect(() => {
    listHabits().then((data) => {
      setHabits(data)
      setLoading(false)
    })
  }, [])

  const visible = useMemo(() => {
    if (filter === 'All') return habits
    return habits.filter((h) => h.timeOfDay === filter.toLowerCase())
  }, [habits, filter])

  const doneCount = habits.filter((h) => h.completed).length

  return (
    <div className="min-h-full bg-surface-dashboard">
      <TopBar filter={filter} onFilterChange={setFilter} filterOptions={FILTERS} />

      <main className="mx-auto max-w-app px-5 pb-28 pt-2">
        <div className="mb-5">
          <h1 className="text-2xl font-bold text-ink">Good day 👋</h1>
          <p className="text-sm text-ink-soft">
            {doneCount} of {habits.length} habits done today
          </p>
        </div>

        <div className="mb-6">
          <WeekStrip />
        </div>

        {loading ? (
          <p className="py-10 text-center text-ink-faint">Loading…</p>
        ) : visible.length === 0 ? (
          <p className="py-10 text-center text-ink-faint">No habits for this filter.</p>
        ) : (
          <div className="flex flex-col gap-3.5">
            {visible.map((habit) => (
              <HabitCard key={habit.id} habit={habit} />
            ))}
          </div>
        )}
      </main>

      <BottomNav />
    </div>
  )
}
