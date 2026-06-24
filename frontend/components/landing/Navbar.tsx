'use client'

import Link from 'next/link'

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-obsidian/80 glass-edge">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-violet-gradient flex items-center justify-center shadow-violet-glow">
            <span className="text-white font-bold text-sm">E</span>
          </div>
          <span className="text-xl font-bold text-frost tracking-tight">
            Evaluator <span className="text-violet-primary">2.0</span>
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-frost-muted text-sm font-medium hover:text-violet-primary transition-colors duration-300">
            Features
          </a>
          <a href="#workflow" className="text-frost-muted text-sm font-medium hover:text-violet-primary transition-colors duration-300">
            How It Works
          </a>
          <a
            href="https://github.com/Izhaar-ahmed/Evaluator"
            target="_blank"
            rel="noopener noreferrer"
            className="text-frost-muted text-sm font-medium hover:text-violet-primary transition-colors duration-300"
          >
            GitHub
          </a>
          <Link
            href="/login"
            className="px-5 py-2.5 rounded-full bg-violet-gradient text-white text-sm font-semibold btn-glow transition-all duration-300 hover:scale-105"
          >
            Try Now
          </Link>
        </div>
      </div>
    </nav>
  )
}
