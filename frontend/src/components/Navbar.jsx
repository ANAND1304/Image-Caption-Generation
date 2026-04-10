
import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Sun, Moon, Zap, History } from 'lucide-react'
import { useThemeStore } from '../hooks/useStore'
import './Navbar.css'

export default function Navbar() {
  const { theme, toggleTheme } = useThemeStore()
  const location = useLocation()

  const links = [
    { to: '/', label: 'Home' },
    { to: '/upload', label: 'Generate' },
    { to: '/history', label: 'History' },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon"><Zap size={18} /></span>
          <span className="brand-name">Caption<span className="brand-accent">AI</span></span>
        </Link>

        <ul className="navbar-links">
          {links.map(({ to, label }) => (
            <li key={to}>
              <Link
                to={to}
                className={`nav-link ${location.pathname === to ? 'active' : ''}`}
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>

        <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </nav>
  )
}
