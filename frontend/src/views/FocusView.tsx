import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ProgressRing from '../components/ProgressRing'
import { getHabit, logProgress, markComplete } from '../api/habits'
import { accentGradient, accentHex } from '../lib/accents'
import type { HabitWithProgress } from '../types'

export default function FocusView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const habitId = Number(id)

  const [habit, setHabit] = useState<HabitWithProgress | null>(null)
  const [step, setStep] = useState('10')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getHabit(habitId).then((h) => {
      if (!h) return
      setHabit(h)
      // Suggest a sensible increment: 1 for small goals, else ~10% of goal.
      setStep(String(h.goal >= 20 ? Math.max(1, Math.round(h.goal / 18)) : 1))
    })
  }, [habitId])

  if (!habit) {
    return (
      <div className="flex min-h-screen items-center justify-center text-ink-faint">Loading…</div>
    )
  }

  const accent = accentHex[habit.accent]
  const ratio = habit.goal > 0 ? habit.progress / habit.goal : 0
  const isQuantity = habit.trackingType === 'quantity'

  async function handleAdd() {
    const amount = Number(step)
    if (!Number.isFinite(amount) || amount === 0) return
    setBusy(true)
    setHabit(await logProgress(habitId, amount, 'increment'))
    setBusy(false)
  }

  async function handleComplete() {
    setBusy(true)
    setHabit(await markComplete(habitId, !habit!.completed))
    setBusy(false)
  }

  return (
    <div className="flex min-h-screen flex-col" style={{ background: accentGradient(habit.accent) }}>
      {/* Header */}
      <header className="mx-auto flex w-full max-w-app items-center justify-between px-5 py-4">
        <button
          type="button"
          aria-label="Back"
          onClick={() => navigate(-1)}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-white/70 text-lg text-ink shadow-card backdrop-blur"
        >
          ‹
        </button>
        <span className="text-sm font-semibold text-ink">{habit.name}</span>
        <Link
          to={`/habit/${habit.id}/edit`}
          aria-label="Edit"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-white/70 text-ink shadow-card backdrop-blur"
        >
          ✎
        </Link>
      </header>

      {/* Centerpiece */}
      <main className="mx-auto flex w-full max-w-app flex-1 flex-col items-center justify-center px-6">
        <ProgressRing progress={ratio} color={accent} size={260} stroke={20}>
          <span className="text-4xl">{habit.emoji}</span>
          <h2 className="mt-1 text-5xl font-bold text-ink">{habit.progress}</h2>
          <span className="text-sm font-medium text-ink-faint">
            / {habit.goal}
            {habit.unit ? ` ${habit.unit}` : ''}
          </span>
        </ProgressRing>

        {habit.completed && (
          <p className="mt-6 text-sm font-semibold" style={{ color: accent }}>
            🎉 Goal reached for today
          </p>
        )}
      </main>

      {/* Actions */}
      <div className="mx-auto w-full max-w-app px-6">
        {isQuantity ? (
          <div className="flex items-center gap-3">
            <input
              value={step}
              onChange={(e) => setStep(e.target.value)}
              inputMode="decimal"
              aria-label="Amount to add"
              className="w-20 rounded-card bg-white/80 py-4 text-center text-lg font-semibold text-ink shadow-card backdrop-blur focus:outline-none"
            />
            <button
              type="button"
              disabled={busy}
              onClick={handleAdd}
              className="flex-1 rounded-card py-4 text-center text-lg font-semibold text-white shadow-card transition-transform active:scale-[0.98] disabled:opacity-60"
              style={{ backgroundColor: accent }}
            >
              Add
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={handleComplete}
              aria-label="Mark complete"
              className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-xl shadow-card transition-transform active:scale-95"
              style={{ color: accent }}
            >
              ✓
            </button>
          </div>
        ) : (
          <button
            type="button"
            disabled={busy}
            onClick={handleComplete}
            className="w-full rounded-card py-4 text-center text-lg font-semibold text-white shadow-card transition-transform active:scale-[0.98]"
            style={{ backgroundColor: habit.completed ? '#94a3b8' : accent }}
          >
            {habit.completed ? 'Undo' : habit.habitType === 'quit' ? 'Stayed clean today' : 'Mark done'}
          </button>
        )}

        {/* Bottom secondary actions */}
        <div className="flex justify-around py-6 text-sm font-medium text-ink-soft">
          <button type="button" className="flex items-center gap-1.5">
            📝 Memo
          </button>
          <button type="button" className="flex items-center gap-1.5">
            📊 Stat
          </button>
        </div>
      </div>
    </div>
  )
}
