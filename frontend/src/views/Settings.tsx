import { useState } from 'react'
import BottomNav from '../components/BottomNav'
import Toggle from '../components/Toggle'

export default function Settings() {
  const [reminders, setReminders] = useState(true)
  const [weekStartMon, setWeekStartMon] = useState(true)
  const [sound, setSound] = useState(false)

  return (
    <div className="min-h-full bg-surface-config">
      <main className="mx-auto max-w-app px-5 pb-28 pt-8">
        <h1 className="mb-5 text-2xl font-bold text-ink">Settings ⚙️</h1>

        <section className="inset-group mb-6">
          <div className="inset-row">
            <span className="text-sm text-ink-soft">Daily reminders</span>
            <Toggle checked={reminders} onChange={setReminders} label="Daily reminders" />
          </div>
          <div className="inset-row">
            <span className="text-sm text-ink-soft">Start week on Monday</span>
            <Toggle checked={weekStartMon} onChange={setWeekStartMon} label="Start week on Monday" />
          </div>
          <div className="inset-row">
            <span className="text-sm text-ink-soft">Completion sound</span>
            <Toggle checked={sound} onChange={setSound} label="Completion sound" />
          </div>
        </section>

        <section className="inset-group">
          <div className="inset-row">
            <span className="text-sm text-ink-soft">Version</span>
            <span className="text-sm font-medium text-ink-faint">0.1.0</span>
          </div>
        </section>
      </main>
      <BottomNav />
    </div>
  )
}
