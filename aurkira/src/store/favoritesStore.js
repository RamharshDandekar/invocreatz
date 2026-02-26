import { create } from 'zustand'

export const useFavoritesStore = create((set) => ({
  items: [],
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  removeItem: (id) => set((state) => ({ items: state.items.filter(i => i.id !== id) })),
  toggleItem: (item) => set((state) => {
    const exists = state.items.find(i => i.id === item.id)
    if (exists) return { items: state.items.filter(i => i.id !== item.id) }
    return { items: [...state.items, item] }
  }),
}))
