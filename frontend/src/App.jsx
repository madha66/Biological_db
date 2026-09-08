import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import HomePage from './pages/HomePage';
import AnalyzePage from './pages/AnalyzePage';
import AboutPage from './pages/AboutPage';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        {/* Navigation */}
        <header className="nav-header">
          <nav className="nav-inner">
            <NavLink to="/" className="nav-brand">
              <div className="logo-icon">K</div>
              KEGGPathRank
            </NavLink>
            <ul className="nav-links">
              <li><NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Home</NavLink></li>
              <li><NavLink to="/analyze" className={({ isActive }) => isActive ? 'active' : ''}>Analyze</NavLink></li>
              <li><NavLink to="/about" className={({ isActive }) => isActive ? 'active' : ''}>About</NavLink></li>
            </ul>
          </nav>
        </header>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="app-footer">
          <p>
            KEGGPathRank v1.0 — Built by Madhan Kumar K., Sanjay J., Sampanna S.
            &nbsp;|&nbsp;
            Data from <a href="https://www.kegg.jp/" target="_blank" rel="noopener noreferrer">KEGG</a>
            &nbsp;|&nbsp;
            For academic use only
          </p>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
