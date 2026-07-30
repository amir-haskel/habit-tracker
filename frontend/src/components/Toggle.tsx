interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  accent?: string
  label?: string
}

// Custom rounded-slider toggle (checkbox styled as a switch).
export default function Toggle({ checked, onChange, accent = '#4fd1c5', label }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className="relative inline-flex h-7 w-12 flex-shrink-0 items-center rounded-pill transition-colors"
      style={{ backgroundColor: checked ? accent : '#e2e8f0' }}
    >
      <span
        className="inline-block h-6 w-6 transform rounded-full bg-white shadow-sm transition-transform"
        style={{ transform: checked ? 'translateX(22px)' : 'translateX(2px)' }}
      />
    </button>
  )
}
