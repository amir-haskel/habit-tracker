import BottomNav from '../components/BottomNav'

// Placeholder — will render 7/30/90-day completion-rate charts from the
// backend's /habits/{id}/stats endpoint once wired.
export default function Stats() {
  return (
    <div className="min-h-full bg-surface-dashboard">
      <main className="mx-auto max-w-app px-5 pb-28 pt-8">
        <h1 className="mb-5 text-2xl font-bold text-ink">Stats 📊</h1>
        <div className="card flex flex-col items-center gap-2 p-10 text-center">
          <span className="text-4xl">📈</span>
          <p className="font-medium text-ink">Completion trends</p>
          <p className="text-sm text-ink-faint">
            7 / 30 / 90-day rates will appear here once the stats API is wired.
          </p>
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
