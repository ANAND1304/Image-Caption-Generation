import React from 'react';
import '../styles/Header.css';

function Header() {
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <div className="logo"><span className="logo-text">CaptionAI</span></div>
          <nav className="nav">
            <a href="#features" className="nav-link">Features</a>
            <a href="#about" className="nav-link">About</a>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header;