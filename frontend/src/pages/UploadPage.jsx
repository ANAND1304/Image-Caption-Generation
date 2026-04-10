
import React, { useCallback } from 'react'
import { Settings2, X } from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'
import ImageDropzone from '../components/ImageDropzone'
import LoadingOrb from '../components/LoadingOrb'
import CaptionResult from '../components/CaptionResult'
import { useSessionStore, useHistoryStore } from '../hooks/useStore'
import { generateCaption } from '../utils/api'
import './UploadPage.css'

export default function UploadPage() {
  const {
    imageFile, imageUrl, caption, confidence, processingTime,
    beamSize, isLoading, error,
    setImage, setBeamSize, setLoading, setResult, setError, reset,
  } = useSessionStore()

  const { addEntry, toggleFavorite, isFavorite } = useHistoryStore()
  const [entryId, setEntryId] = React.useState(null)
  const [showSettings, setShowSettings] = React.useState(false)

  const handleFile = useCallback((file) => {
    const url = URL.createObjectURL(file)
    setImage(file, url)
    setEntryId(null)
  }, [setImage])

  const handleGenerate = async () => {
    if (!imageFile) return
    setLoading(true)
    try {
      const result = await generateCaption(imageFile, beamSize)
      setResult(result)
      const id = Date.now().toString()
      setEntryId(id)
      addEntry({ id, imageUrl, caption: result.caption, confidence: result.confidence, timestamp: Date.now() })
      toast.success('Caption generated!')
    } catch (err) {
      setError(err.message)
      toast.error(err.message)
    }
  }

  const handleReset = () => {
    if (imageUrl) URL.revokeObjectURL(imageUrl)
    reset()
    setEntryId(null)
  }

  return (
    <div className="upload-page">
      <Toaster position="top-right" toastOptions={{
        style: { background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border)' }
      }} />

      <div className="upload-inner">
        <div className="page-header">
          <h1 className="page-title">Generate Caption</h1>
          <p className="page-sub">Upload an image and our AI will describe it in natural language.</p>
        </div>

        <div className="upload-card">
          {/* No image yet */}
          {!imageUrl && !isLoading && !caption && (
            <ImageDropzone onFile={handleFile} disabled={isLoading} />
          )}

          {/* Image selected, not yet generated */}
          {imageUrl && !isLoading && !caption && (
            <div className="preview-area">
              <div className="preview-img-wrap">
                <img src={imageUrl} alt="Preview" className="preview-img" />
                <button className="preview-remove" onClick={handleReset} title="Remove">
                  <X size={14} />
                </button>
              </div>

              <div className="preview-controls">
                <div className="beam-control">
                  <button
                    className="settings-toggle"
                    onClick={() => setShowSettings(s => !s)}
                  >
                    <Settings2 size={14} />
                    Beam Size: {beamSize}
                  </button>
                  {showSettings && (
                    <div className="beam-panel">
                      <p className="beam-label">Beam Search Width</p>
                      <div className="beam-options">
                        {[1, 2, 3, 4, 5].map(n => (
                          <button
                            key={n}
                            className={`beam-opt ${beamSize === n ? 'active' : ''}`}
                            onClick={() => { setBeamSize(n); setShowSettings(false) }}
                          >
                            {n}
                          </button>
                        ))}
                      </div>
                      <p className="beam-hint">Higher = better quality, slower inference</p>
                    </div>
                  )}
                </div>

                <button className="generate-btn" onClick={handleGenerate}>
                  <span className="generate-icon">⚡</span>
                  Generate Caption
                </button>
              </div>
            </div>
          )}

          {/* Loading */}
          {isLoading && <LoadingOrb />}

          {/* Error */}
          {error && !isLoading && (
            <div className="error-box">
              <p className="error-title">Something went wrong</p>
              <p className="error-msg">{error}</p>
              <button className="btn-reset" onClick={handleReset}>Try Again</button>
            </div>
          )}

          {/* Result */}
          {caption && !isLoading && (
            <CaptionResult
              imageUrl={imageUrl}
              caption={caption}
              confidence={confidence}
              processingTime={processingTime}
              onReset={handleReset}
              onFavorite={() => entryId && toggleFavorite(entryId)}
              isFavorite={entryId ? isFavorite(entryId) : false}
            />
          )}
        </div>

        {/* Drop hint when result shown */}
        {caption && !isLoading && (
          <p className="drop-another">
            Want to try another image?{' '}
            <button className="link-btn" onClick={handleReset}>Upload a new one →</button>
          </p>
        )}
      </div>
    </div>
  )
}
