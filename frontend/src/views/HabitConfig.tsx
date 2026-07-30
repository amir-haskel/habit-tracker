import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import PillSelector from '../components/PillSelector'
import Toggle from '../components/Toggle'
import { getHabit } from '../api/habits'
import { accentHex } from '../lib/accents'
import type { AccentColor, HabitType, TimeOfDay, TrackingType } from '../types'

const EMOJIS = ['🏋️', '📘', '🥛', '🛏️', '🧘', '🌙', '💧', '🏃', '📖', '🎯']
const ACCENTS: AccentColor[] = ['orange', 'blue', 'mint', 'purple', 'pink']

const HABIT_TYPES = [
  { value: 'build' as HabitType, label: 'Build 🌱' },
  { value: 'quit' as HabitType, label: 'Quit 🚫' },
]
const TRACKING_TYPES = [
  { value: 'boolean' as TrackingType, label: 'Checkmark' },
  { value: 'quantity' as TrackingType, label: 'Quantity' },
]
const TIMES = [
  { value: 'anytime' as TimeOfDay, label: 'Anytime' },
  { value: 'morning' as TimeOfDay, label: 'Morning' },
  { value: 'afternoon' as TimeOfDay, label: 'Afternoon' },
  { value: 'evening' as TimeOfDay, label: 'Evening' },
]

export default function HabitConfig() {
  const navigate = useNavigate()
  const { id } = useParams()
  const isEdit = Boolean(id)

  const [name, setName] = useState('')
  const [emoji, setEmoji] = useState('🎯')
  const [accent, setAccent] = useState<AccentColor>('purple')
  const [habitType, setHabitType] = useState<HabitType>('build')
  const [trackingType, setTrackingType] = useState<TrackingType>('quantity')
  const [target, setTarget] = useState('7')
  const [unit, setUnit] = useState('h')
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>('anytime')
  const [reminder, setReminder] = useState(false)

  useEffect(() => {
    if (!id) return
    getHabit(Number(id)).then((h) => {
      if (!h) return
      setName(h.name)
      setEmoji(h.emoji)
      setAccent(h.accent)
      setHabitType(h.habitType)
      setTrackingType(h.trackingType)
      setTarget(h.targetValue != null ? String(h.targetValue) : '')
      setUnit(h.unit ?? '')
      setTimeOfDay(h.timeOfDay)
      setReminder(h.reminderEnabled)
    })
  }, [id])

  const accentColor = accentHex[accent]

  function handleSave() {
    // MOCK: persistence not wired. In live mode this POSTs/PATCHes /habits.
    navigate('/')
  }

  return (
    <div className="min-h-full bg-surface-config pb-10">
      {/* Header */}
      <header className="sticky top-0 z-10 frosted">
        <div className="mx-auto grid max-w-app grid-cols-[auto_1fr_auto] items-center px-4 py-3">
          <button
            type="button"
            aria-label="Back"
            onClick={() => navigate(-1)}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-lg text-ink shadow-card"
          >
            ‹
          </button>
          <div className="flex flex-col items-center">
            <span className="text-2xl leading-none">{emoji}</span>
            <span className="mt-0.5 text-sm font-semibold text-ink">
              {isEdit ? 'Edit Habit' : 'New Habit'}
            </span>
          </div>
          <span className="w-9" />
        </div>
      </header>

      <main className="mx-auto flex max-w-app flex-col gap-6 px-5 pt-4">
        {/* Basics */}
        <section className="inset-group">
          <div className="inset-row">
            <label htmlFor="name" className="text-sm text-ink-soft">
              Name
            </label>
            <input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Drink water"
              className="w-1/2 bg-transparent text-right text-sm font-medium text-ink placeholder:text-ink-faint focus:outline-none"
            />
          </div>

          <div className="px-4 py-3.5">
            <p className="mb-2 text-sm text-ink-soft">Icon</p>
            <div className="no-scrollbar flex gap-2 overflow-x-auto">
              {EMOJIS.map((e) => (
                <button
                  key={e}
                  type="button"
                  onClick={() => setEmoji(e)}
                  className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl text-xl transition-transform active:scale-95"
                  style={{
                    backgroundColor: emoji === e ? accentColor : '#f1f5f9',
                  }}
                >
                  {e}
                </button>
              ))}
            </div>
          </div>

          <div className="inset-row">
            <span className="text-sm text-ink-soft">Color</span>
            <div className="flex gap-2">
              {ACCENTS.map((c) => (
                <button
                  key={c}
                  type="button"
                  aria-label={c}
                  onClick={() => setAccent(c)}
                  className="h-7 w-7 rounded-full transition-transform active:scale-90"
                  style={{
                    backgroundColor: accentHex[c],
                    outline: accent === c ? `2px solid ${accentHex[c]}` : 'none',
                    outlineOffset: 2,
                  }}
                />
              ))}
            </div>
          </div>
        </section>

        {/* Type */}
        <section className="inset-group">
          <div className="flex flex-col gap-2.5 px-4 py-3.5">
            <span className="text-sm text-ink-soft">Habit type</span>
            <PillSelector options={HABIT_TYPES} value={habitType} onChange={setHabitType} accent={accentColor} />
          </div>
          <div className="flex flex-col gap-2.5 border-t border-slate-100 px-4 py-3.5">
            <span className="text-sm text-ink-soft">Tracking</span>
            <PillSelector
              options={TRACKING_TYPES}
              value={trackingType}
              onChange={setTrackingType}
              accent={accentColor}
            />
          </div>
        </section>

        {/* Goal (quantity only) */}
        {trackingType === 'quantity' && (
          <section className="inset-group">
            <div className="inset-row">
              <span className="text-sm text-ink-soft">Daily goal</span>
              <div className="flex items-center gap-1.5">
                <input
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  inputMode="decimal"
                  className="w-16 rounded-lg bg-slate-50 py-1 text-center text-sm font-semibold text-ink focus:outline-none"
                />
                <input
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="unit"
                  className="w-16 rounded-lg bg-slate-50 py-1 text-center text-sm font-medium text-ink placeholder:text-ink-faint focus:outline-none"
                />
                <span className="text-sm text-ink-faint">/ day</span>
              </div>
            </div>
          </section>
        )}

        {/* Schedule */}
        <section className="inset-group">
          <div className="flex flex-col gap-2.5 px-4 py-3.5">
            <span className="text-sm text-ink-soft">Time of day</span>
            <PillSelector options={TIMES} value={timeOfDay} onChange={setTimeOfDay} accent={accentColor} />
          </div>
          <div className="inset-row border-t border-slate-100">
            <span className="text-sm text-ink-soft">Reminder</span>
            <Toggle checked={reminder} onChange={setReminder} accent={accentColor} label="Reminder" />
          </div>
        </section>

        <button
          type="button"
          onClick={handleSave}
          className="mt-1 w-full rounded-card py-4 text-center font-semibold text-white shadow-card transition-transform active:scale-[0.98]"
          style={{ backgroundColor: accentColor }}
        >
          {isEdit ? 'Save Changes' : 'Create Habit'}
        </button>
      </main>
    </div>
  )
}
