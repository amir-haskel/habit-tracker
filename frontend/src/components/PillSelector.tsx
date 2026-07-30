interface PillSelectorProps<T extends string> {
  options: readonly { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
  accent?: string
}

// Horizontal row of pill-shaped options — a friendlier radio-button group.
export default function PillSelector<T extends string>({
  options,
  value,
  onChange,
  accent = '#a78bfa',
}: PillSelectorProps<T>) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const active = opt.value === value
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`pill ${active ? '' : 'pill-inactive'}`}
            style={active ? { backgroundColor: accent, color: 'white' } : undefined}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
