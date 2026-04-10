
import React, { useState, useEffect } from 'react'
import { Copy, Check, Download, RefreshCw, Star, Clock, Cpu, BarChart2 } from 'lucide-react'
import toast from 'react-hot-toast'
import './CaptionResult.css'

function TypewriterText({ text, speed = 40 }) {
  const [displayed, setDisplayed] = useState('')
  useEffect(() => {
    setDisplayed('')
    if (!text) return
    let i = 0
    const id = setInterval(() => {
      setDisplayed(text.slice(0, i + 1))
      i++
      if (i >= text.length) clearInterval(id)
    }, speed)
    return () => clearInterval(id)
  }, [text, speed])
  return <span>{displayed}<span className="cursor">|</span></span>
}

export default function CaptionResult({
  imageUrl, caption, confidence, processingTime,
  onReset, onFavorite, isFavorite,
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(caption)
    setCopied(true)
    toast.success('Caption copied!')
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([caption], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'caption.txt'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Caption downloaded!')
  }

  const confPct = Math.round((confidence || 0) * 100)
  const confColor = confPct >= 80 ? '#10b981' : confPct >= 60 ? '#f59e0b' : '#ef4444'

  return (
    <div className="result-layout">
      {/* Image panel */}
      <div className="result-image-panel">
        <img src={imageUrl} alt="Uploaded" className="result-img" />
        <div className="result-img-overlay">
          <span className="result-img-badge">Analyzed ✓</span>
        </div>
      </div>

      {/* Caption panel */}
      <div className="result-content">
        <div className="result-label">
          <span className="label-dot" />
          Generated Caption
        </div>

        <blockquote className="caption-text">
          <TypewriterText text={caption} />
        </blockquote>

        {/* Stats row */}
        <div className="result-stats">
          <div className="stat-chip">
            <BarChart2 size={13} />
            <span>Confidence</span>
            <span className="stat-value" style={{ color: confColor }}>{confPct}%</span>
          </div>
          <div className="stat-chip">
            <Clock size={13} />
            <span>{processingTime}ms</span>
          </div>
          <div className="stat-chip">
            <Cpu size={13} />
            <span>Beam Search</span>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="conf-bar-wrap">
          <div className="conf-bar">
            <div
              className="conf-fill"
              style={{ width: `${confPct}%`, background: confColor }}
            />
          </div>
        </div>

        {/* Action buttons */}
        <div className="result-actions">
          <button className="action-btn primary" onClick={handleCopy}>
            {copied ? <Check size={15} /> : <Copy size={15} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button className="action-btn" onClick={handleDownload}>
            <Download size={15} /> Download
          </button>
          <button
            className={`action-btn ${isFavorite ? 'favorited' : ''}`}
            onClick={onFavorite}
          >
            <Star size={15} fill={isFavorite ? 'currentColor' : 'none'} />
            {isFavorite ? 'Saved' : 'Save'}
          </button>
          <button className="action-btn reset" onClick={onReset}>
            <RefreshCw size={15} /> New Image
          </button>
        </div>
      </div>
    </div>
  )
}
