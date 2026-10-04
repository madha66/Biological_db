import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

export function PathWeaveLogo({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="PathWeave logo"
    >
      <defs>
        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0ECFCF" />
          <stop offset="100%" stopColor="#7C3AED" />
        </linearGradient>
      </defs>
      <path d="M4 6 Q 10 14 16 16" stroke="url(#logoGrad)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M28 6 Q 22 14 16 16" stroke="url(#logoGrad)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M16 4 Q 16 10 16 16" stroke="url(#logoGrad)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <circle cx="16" cy="16" r="3.5" fill="url(#logoGrad)" />
      <path d="M16 16 Q 10 22 6 28" stroke="url(#logoGrad)" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.7" />
      <path d="M16 16 Q 22 22 26 28" stroke="url(#logoGrad)" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.7" />
      <path d="M16 16 Q 16 23 16 29" stroke="url(#logoGrad)" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.7" />
    </svg>
  );
}

export function Header() {
  const location = useLocation();

  const navItems = [
    { label: 'Analyze', path: '/' },
    { label: 'About', path: '/about' },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-border-subtle bg-bg-primary/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Wordmark */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <motion.div
            whileHover={{ rotate: 5 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <PathWeaveLogo size={30} />
          </motion.div>
          <span className="text-xl font-semibold tracking-tight">
            <span className="gradient-text">PathWeave</span>
          </span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1" aria-label="Main navigation">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150
                  ${isActive
                    ? 'bg-bg-tertiary text-white'
                    : 'text-slate-400 hover:text-white hover:bg-bg-tertiary/50'
                  }
                `}
                aria-current={isActive ? 'page' : undefined}
              >
                {item.label}
              </Link>
            );
          })}
          <a
            href="https://github.com/pathweave"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-bg-tertiary/50 transition-all duration-150"
            aria-label="PathWeave on GitHub"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
