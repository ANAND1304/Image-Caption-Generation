import React from 'react';
import '../styles/Features.css';

function Features() {
  return (
    <section id="features" className="features-section">
      <div className="container">
        <h2>Advanced AI Technology</h2>
        <p>Built with InceptionV3 CNN + LSTM Networks</p>
        <div className="features-grid">
          <div className="feature-card">
            <div className="icon">🧠</div>
            <h3>Deep Learning</h3>
            <p>CNN + LSTM architecture</p>
          </div>
          <div className="feature-card">
            <div className="icon">⚡</div>
            <h3>Fast Processing</h3>
            <p>Real-time captions</p>
          </div>
          <div className="feature-card">
            <div className="icon">🎯</div>
            <h3>High Accuracy</h3>
            <p>BLEU evaluated</p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Features;