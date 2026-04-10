
import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Zap, Brain, Globe, Lock } from 'lucide-react'
import './HomePage.css'

const FEATURES = [
  { icon: Brain, title: 'Attention Mechanism', desc: 'ResNet50 + LSTM with Bahdanau attention focuses on the most relevant image regions.' },
  { icon: Zap, title: 'Beam Search Decoding', desc: 'Multi-path beam search produces more fluent and accurate captions than greedy decoding.' },
  { icon: Globe, title: 'BLEU-4 Optimized', desc: 'Trained and evaluated with BLEU-1 through BLEU-4 metrics on Flickr8k dataset.' },
  { icon: Lock, title: 'Production Ready', desc: 'Redis caching, rate limiting, Docker containerization, and CI/CD ready.' },
]

const EXAMPLES = [
  { caption: 'a dog running across a green field with a ball in its mouth' },
  { caption: 'two children playing on a wooden playground structure' },
  { caption: 'a woman in a red dress standing near a waterfall' },
  { caption: 'a group of cyclists riding along a mountain trail at sunset' },
]

export default function HomePage() {
  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <div className="hero-glow" />
        <div className="hero-inner">
          <div className="hero-badge">
            <span className="badge-dot" />
            Deep Learning · ResNet50 · LSTM · Attention
          </div>
          <h1 className="hero-title">
            Turn Any Image<br />
            Into <span className="hero-accent">Words</span>
          </h1>
          <p className="hero-sub">
            Upload a photo and watch our CNN + LSTM model analyze it in real-time,
            generating a natural language caption using attention-based deep learning.
          </p>
          <div className="hero-cta">
            <Link to="/upload" className="btn-primary">
              Try It Now <ArrowRight size={16} />
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
            >
              View on GitHub
            </a>
          </div>

          {/* Floating caption examples */}
          <div className="example-captions">
            {EXAMPLES.map((ex, i) => (
              <div key={i} className="ex-caption" style={{ animationDelay: `${i * 0.15}s` }}>
                <span className="ex-quote">"</span>
                {ex.caption}
                <span className="ex-quote">"</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture diagram */}
      <section className="arch-section">
        <div className="section-inner">
          <p className="section-label">Architecture</p>
          <h2 className="section-title">How It Works</h2>
          <div className="arch-flow">
            {[
              { step: '01', label: 'Image Input', sub: 'JPEG · PNG · WEBP' },
              { step: '02', label: 'ResNet50', sub: 'Feature Extraction' },
              { step: '03', label: 'Attention', sub: 'Region Weighting' },
              { step: '04', label: 'LSTM', sub: 'Sequence Generation' },
              { step: '05', label: 'Beam Search', sub: 'Caption Selection' },
            ].map((s, i) => (
              <React.Fragment key={i}>
                <div className="arch-node">
                  <div className="arch-num">{s.step}</div>
                  <div className="arch-label">{s.label}</div>
                  <div className="arch-sub">{s.sub}</div>
                </div>
                {i < 4 && <div className="arch-arrow">→</div>}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features-section">
        <div className="section-inner">
          <p className="section-label">Features</p>
          <h2 className="section-title">Production-Grade AI</h2>
          <div className="features-grid">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="feature-card">
                <div className="feature-icon"><Icon size={20} /></div>
                <h3 className="feature-title">{title}</h3>
                <p className="feature-desc">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="cta-inner">
          <h2 className="cta-title">Ready to caption your images?</h2>
          <p className="cta-sub">No signup required. Just upload and generate.</p>
          <Link to="/upload" className="btn-primary large">
            Start Generating <ArrowRight size={18} />
          </Link>
        </div>
      </section>
    </div>
  )
}
