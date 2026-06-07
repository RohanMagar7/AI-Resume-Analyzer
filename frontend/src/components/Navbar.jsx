import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navbar() {
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/' ? 'active' : '';
    return location.pathname.startsWith(path) ? 'active' : '';
  };

  return (
    <nav className="navbar">
      <div className="container">
        <Link to="/" className="navbar-brand">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 12h6M12 9v6M3 12a9 9 0 1 1 18 0 9 9 0 0 1-18 0z" />
          </svg>
          <span>AI Resume Analyzer</span>
        </Link>
        <div className="nav-links">
          <Link to="/" className={`nav-link ${isActive('/')}`}>
            Dashboard
          </Link>
          <Link to="/upload" className={`nav-link ${isActive('/upload')}`}>
            Upload Resume
          </Link>
          <Link to="/resumes" className={`nav-link ${isActive('/resumes')}`}>
            Resume List
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;