import { NavLink, useNavigate } from 'react-router-dom'

const items = [
  { to: '/', icon: '🏠', label: 'Home', end: true },
  { to: '/stats', icon: '📊', label: 'Stats', end: false },
  { to: '/settings', icon: '⚙️', label: 'Settings', end: false },
]

// Fixed translucent frosted-glass bottom navigation.
export default function BottomNav() {
  const navigate = useNavigate()

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 frosted border-t border-white/60">
      <div className="mx-auto flex max-w-app items-center justify-around px-6 py-2.5">
        {items.slice(0, 1).map((item) => (
          <NavItem key={item.to} {...item} />
        ))}

        {/* Center "add habit" action */}
        <button
          type="button"
          aria-label="New habit"
          onClick={() => navigate('/new')}
          className="-mt-6 flex h-14 w-14 items-center justify-center rounded-full bg-ink text-2xl text-white shadow-card-hover transition-transform active:scale-95"
        >
          +
        </button>

        {items.slice(1).map((item) => (
          <NavItem key={item.to} {...item} />
        ))}
      </div>
    </nav>
  )
}

function NavItem({ to, icon, label, end }: { to: string; icon: string; label: string; end: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className="flex flex-col items-center gap-0.5"
    >
      {({ isActive }) => (
        <>
          <span className={`text-xl transition-opacity ${isActive ? 'opacity-100' : 'opacity-40'}`}>
            {icon}
          </span>
          <span className={`text-[10px] font-medium ${isActive ? 'text-ink' : 'text-ink-faint'}`}>
            {label}
          </span>
        </>
      )}
    </NavLink>
  )
}
