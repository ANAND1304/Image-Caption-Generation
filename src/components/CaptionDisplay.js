import React, { useState } from 'react';
import '../styles/CaptionDisplay.css';

function CaptionDisplay({ image, caption, loading, error, onReset }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="caption-display">
      <div className="result-container">
        <div className="image-preview">
          <img src={image} alt="Uploaded" />
        </div>
        <div className="caption-section">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Analyzing with Deep Learning...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <p>{error}</p>
              <button onClick={onReset}>Try Again</button>
            </div>
          ) : caption ? (
            <div className="caption-result">
              <h3>Generated Caption</h3>
              <div className="caption-text"><p>{caption}</p></div>
              <div className="caption-actions">
                <button onClick={handleCopy} className="copy-button">
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
                <button onClick={onReset} className="reset-button">🔄 New Image</button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default CaptionDisplay;