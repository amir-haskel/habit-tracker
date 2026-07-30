import { mockHabits } from '../data/mockData'
import type { HabitWithProgress } from '../types'
// import { apiFetch } from './client'  // ← uncomment when wiring the real backend

// ---------------------------------------------------------------------------
// MOCK MODE
// In-memory store seeded from mockData. Every function below mirrors a future
// backend endpoint; the commented `apiFetch` line shows the real call so
// swapping mock → live is a one-line change per function.
// ---------------------------------------------------------------------------

let habits: HabitWithProgress[] = mockHabits.map((h) => ({ ...h }))

export async function listHabits(): Promise<HabitWithProgress[]> {
  // return apiFetch<HabitWithProgress[]>('/habits')
  return habits.filter((h) => !h.isArchived).map((h) => ({ ...h }))
}

export async function getHabit(id: number): Promise<HabitWithProgress | undefined> {
  // return apiFetch<HabitWithProgress>(`/habits/${id}`)
  const found = habits.find((h) => h.id === id)
  return found ? { ...found } : undefined
}

// Log quantity progress for today. mode "increment" adds; "set" overwrites.
export async function logProgress(
  id: number,
  amount: number,
  mode: 'increment' | 'set' = 'increment',
): Promise<HabitWithProgress> {
  // const isoToday = new Date().toISOString().slice(0, 10)
  // return apiFetch(`/habits/${id}/logs`, {
  //   method: 'POST',
  //   body: JSON.stringify({ date: isoToday, amount, mode }),
  // })
  const habit = habits.find((h) => h.id === id)
  if (!habit) throw new Error(`Habit ${id} not found`)
  habit.progress = mode === 'set' ? amount : habit.progress + amount
  habit.completed = habit.progress >= habit.goal
  return { ...habit }
}

// Mark a boolean (or quick-complete a quantity) habit done for today.
export async function markComplete(id: number, done: boolean): Promise<HabitWithProgress> {
  // const isoToday = new Date().toISOString().slice(0, 10)
  // return apiFetch(`/habits/${id}/logs`, {
  //   method: 'POST',
  //   body: JSON.stringify({ date: isoToday, completed: done }),
  // })
  const habit = habits.find((h) => h.id === id)
  if (!habit) throw new Error(`Habit ${id} not found`)
  habit.completed = done
  habit.progress = done ? habit.goal : 0
  return { ...habit }
}

// Reset the in-memory store (used by nothing yet; handy for tests/storybook).
export function __resetMockStore() {
  habits = mockHabits.map((h) => ({ ...h }))
}
