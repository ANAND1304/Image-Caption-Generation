import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useThemeStore = create(
  persist(
    (set) => ({
      theme: 'dark',
      toggleTheme: () =>
        set((s) => {
          const next = s.theme === 'dark' ? 'light' : 'dark'
          document.documentElement.setAttribute('data-theme', next)
          return { theme: next }
        }),
    }),
    { name: 'caption-theme' }
  )
)

export const useHistoryStore = create(
  persist(
    (set, get) => ({
      history: [],
      favorites: [],
      addEntry: (entry) =>
        set((s) => ({ history: [entry, ...s.history].slice(0, 50) })),
      toggleFavorite: (id) =>
        set((s) => {
          const favs = s.favorites.includes(id)
            ? s.favorites.filter(f => f !== id)
            : [...s.favorites, id]
          return { favorites: favs }
        }),
      clearHistory: () => set({ history: [], favorites: [] }),
      isFavorite: (id) => get().favorites.includes(id),
    }),
    { name: 'caption-history' }
  )
)

export const useSessionStore = create((set) => ({
  imageFile: null,
  imageUrl: null,
  caption: null,
  confidence: null,
  processingTime: null,
  beamSize: 3,
  isLoading: false,
  error: null,
  setImage: (file, url) => set({ imageFile: file, imageUrl: url, caption: null, error: null }),
  setBeamSize: (b) => set({ beamSize: b }),
  setLoading: (v) => set({ isLoading: v }),
  setResult: (r) => set({
    caption: r.caption,
    confidence: r.confidence,
    processingTime: r.processing_time_ms,
    isLoading: false,
    error: null,
  }),
  setError: (e) => set({ error: e, isLoading: false }),
  reset: () => set({
    imageFile: null, imageUrl: null, caption: null,
    confidence: null, processingTime: null,
    isLoading: false, error: null,
  }),
}))
