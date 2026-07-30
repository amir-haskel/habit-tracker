import type { AccentColor } from '../types'

// Single source of truth for each accent's base hue. We derive tints/gradients
// from these at runtime (inline styles) rather than composing Tailwind class
// names dynamically — Tailwind purges classes it can't see as literals.
export const accentHex: Record<AccentColor, string> = {
  orange: '#f9a03f',
  blue: '#5aa9e6',
  mint: '#4fd1c5',
  purple: '#a78bfa',
  pink: '#f472b6',
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

// Soft translucent tint of an accent — for card backgrounds & pills.
export function tint(color: AccentColor, alpha: number): string {
  const [r, g, b] = hexToRgb(accentHex[color])
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// Full-viewport gradient for the Focus view background.
export function accentGradient(color: AccentColor): string {
  return `radial-gradient(circle at 50% 22%, ${tint(color, 0.28)} 0%, ${tint(color, 0.1)} 42%, #f7f7fb 100%)`
}
