'use client'

import Link from 'next/link'

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden py-24 md:py-32">
      {/* Background Glow Effects */}
      <div className="absolute inset-0 bg-hero-glow opacity-60" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-violet-deep/10 blur-[120px] animate-glow" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full bg-emerald-trust/5 blur-[100px] animate-glow stagger-2" />

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-surface ghost-border mb-8 animate-fade-in">
          <span className="w-2 h-2 rounded-full bg-emerald-trust animate-glow" />
          <span className="text-frost-muted text-xs font-grotesk font-medium tracking-wide uppercase">
            AI-Powered Academic Evaluation
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-frost leading-[1.1] tracking-tight mb-6 animate-slide-up">
          Intelligent Evaluation for{' '}
          <span className="bg-violet-gradient bg-clip-text text-transparent">
            Student Code & Content
          </span>
        </h1>

        {/* Subtext */}
        <p className="text-frost-muted text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mb-10 animate-slide-up stagger-2 opacity-0">
          Automate rigorous academic grading with our proprietary multi-agent approach.
          Conditional Scoring, Strict Relevance Checks, and LLM-powered feedback — delivering
          human-level insights in milliseconds.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-slide-up stagger-3 opacity-0">
          <Link
            href="/login"
            className="px-8 py-4 rounded-full bg-violet-gradient text-white font-semibold text-base btn-glow transition-all duration-300 hover:scale-105 hover:shadow-violet-glow-lg"
          >
            Start Evaluating
          </Link>
          <a
            href="#workflow"
            className="px-8 py-4 rounded-full ghost-border text-violet-primary font-semibold text-base transition-all duration-300 hover:bg-slate-surface hover:border-violet-deep/30"
          >
            View Demo
          </a>
        </div>

        {/* Decorative Dashboard Preview */}
        <div className="mt-16 animate-slide-up stagger-4 opacity-0">
          <div className="relative max-w-3xl mx-auto rounded-2xl bg-slate-surface glass-edge p-1 shadow-ambient">
            <div className="rounded-xl bg-obsidian p-6 space-y-4">
              {/* Fake dashboard toolbar */}
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-coral-container/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                <div className="w-3 h-3 rounded-full bg-emerald_trust/60" />
                <div className="ml-4 flex-1 h-6 rounded-full bg-slate-surface-high/60" />
              </div>
              {/* Fake evaluation rows */}
              <div className="space-y-3">
                {[
                  { name: 'student_01.py', score: 92, color: 'bg-emerald_trust' },
                  { name: 'report_analysis.txt', score: 78, color: 'bg-violet-container' },
                  { name: 'algorithm_hw3.cpp', score: 85, color: 'bg-emerald_trust' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-slate-surface-high/40">
                    <span className="text-frost-muted font-grotesk text-sm w-40 truncate">{item.name}</span>
                    <div className="flex-1 h-2 rounded-full bg-obsidian-deep">
                      <div
                        className={`h-full rounded-full ${item.color} transition-all duration-1000`}
                        style={{ width: `${item.score}%` }}
                      />
                    </div>
                    <span className="text-frost font-bold text-sm font-grotesk w-10 text-right">{item.score}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
