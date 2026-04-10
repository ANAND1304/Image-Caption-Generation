
import React, { useState } from 'react'
import { Star, Trash2, Clock, Copy, Check } from 'lucide-react'
import { useHistoryStore } from '../hooks/useStore'
import toast, { Toaster } from 'react-hot-toast'
import './HistoryPage.css'

function HistoryCard({ entry, isFav, onToggleFav }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(entry.caption)
    setCopied(true)
    toast.success('Copied!')
    setTimeout(() => setCopied(false), 2000)
  }

  const timeAgo = (ts) => {
    const diff = Date.now() - ts
    const m = Math.floor(diff / 60000)
    const h = Math.floor(m / 60)
    const d = Math.floor(h / 24)
    if (d > 0) return `${d}d ago`
    if (h > 0) return `${h}h ago`
    if (m > 0) return `${m}m ago`
    return 'just now'
  }

  return (
    <div className={`history-card ${isFav ? 'favorited' : ''}`}>
      <div className="hcard-image">
        <img src={entry.imageUrl} alt="Caption" />
        {isFav && <div className="fav-badge"><Star size={10} fill="currentColor" /></div>}
      </div>
      <div className="hcard-content">
        <p className="hcard-caption">"{entry.caption}"</p>
        <div className="hcard-meta">
          <span className="hcard-time"><Clock size={11} /> {timeAgo(entry.timestamp)}</span>
          <span className="hcard-conf">{Math.round((entry.confidence || 0) * 100)}% confidence</span>
        </div>
        <div className="hcard-actions">
          <button className="hcard-btn" onClick={handleCopy}>
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </button>
          <button
            className={`hcard-btn ${isFav ? 'is-fav' : ''}`}
            onClick={() => onToggleFav(entry.id)}
          >
            <Star size={13} fill={isFav ? 'currentColor' : 'none'} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default function HistoryPage() {
  const { history, favorites, toggleFavorite, clearHistory, isFavorite } = useHistoryStore()
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'favorites'
    ? history.filter(e => isFavorite(e.id))
    : history

  return (
    <div className="history-page">
      <Toaster position="top-right" toastOptions={{
        style: { background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)' }
      }} />
      <div className="history-inner">
        <div className="history-header">
          <div>
            <h1 className="page-title">History</h1>
            <p className="page-sub">{history.length} captions generated</p>
          </div>
          <div className="history-controls">
            <div className="filter-tabs">
              {['all', 'favorites'].map(f => (
                <button
                  key={f}
                  className={`filter-tab ${filter === f ? 'active' : ''}`}
                  onClick={() => setFilter(f)}
                >
                  {f === 'favorites' ? <Star size={13} /> : null}
                  {f === 'all' ? 'All' : 'Favorites'}
                </button>
              ))}
            </div>
            {history.length > 0 && (
              <button
                className="clear-btn"
                onClick={() => { if (window.confirm('Clear all history?')) clearHistory() }}
              >
                <Trash2 size={14} /> Clear All
              </button>
            )}
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">{filter === 'favorites' ? '⭐' : '🖼️'}</div>
            <p className="empty-title">
              {filter === 'favorites' ? 'No favorites yet' : 'No history yet'}
            </p>
            <p className="empty-sub">
              {filter === 'favorites'
                ? 'Star captions you love to save them here.'
                : 'Generate your first caption to see it here.'}
            </p>
          </div>
        ) : (
          <div className="history-grid">
            {filtered.map(entry => (
              <HistoryCard
                key={entry.id}
                entry={entry}
                isFav={isFavorite(entry.id)}
                onToggleFav={toggleFavorite}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
