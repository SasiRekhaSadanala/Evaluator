'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import StudentNavbar from '@/components/StudentNavbar'
import { AuthStore } from '@/lib/auth-store'
import { API_BASE } from '@/lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ProgressData {
  student_id: string
  score_history: { assignment_id: string; topic_tag: string; score: number; submitted_at: string }[]
  summary: {
    total_submissions: number; average_score: number; best_score: number
    worst_score: number; cumulative_grade: string; gpa: number
  }
  skill_breakdown: { topic_tag: string; avg_score: number; submission_count: number }[]
  class_rank: { percentile: number; class_size: number; student_avg: number | null }
  improvement: { delta: number | null; trend: string; prev_avg: number | null }
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */


const SKILL_COLORS = ['bg-violet-primary', 'bg-emerald-trust', 'bg-violet-container', 'bg-cyan-400', 'bg-amber-400', 'bg-rose-400']

function trendBadgeBg(trend: string) {
  if (trend === 'improving') return 'bg-emerald-trust/10 border-emerald-trust/20 text-emerald-trust'
  if (trend === 'declining') return 'bg-coral/10 border-coral/20 text-coral'
  return 'bg-frost-muted/10 border-frost-muted/20 text-frost-muted'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function ProgressPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<ProgressData | null>(null)

  useEffect(() => {
    const { isAuthenticated, user } = AuthStore.getState()
    if (!isAuthenticated || user?.role !== 'student') {
      router.push('/login')
      return
    }

    const fetchProgress = async () => {
      try {
        const res = await AuthStore.fetchAuth(`${API_BASE}/api/portal/progress`)
        if (res.ok) {
          const json = await res.json()
          if (json.status === 'success') setData(json)
        }
      } catch {
        // Silently handle
      } finally {
        setLoading(false)
      }
    }
    fetchProgress()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-violet-primary/30 border-t-violet-primary rounded-full animate-spin" />
          <p className="text-sm text-frost-muted">Loading progress data...</p>
        </div>
      </div>
    )
  }

  const hasData = data && data.summary.total_submissions > 0

  // Prepare chart data
  const chronological = hasData ? [...data.score_history].reverse() : []
  const maxScore = 100
  const barData = chronological.map(h => ({
    height: `${Math.max(5, (h.score / maxScore) * 100)}%`,
    score: h.score,
    label: formatDate(h.submitted_at),
    topic: h.topic_tag || 'General',
  }))

  // SVG trend line
  const svgW = 1000, svgH = 200
  const svgPoints = chronological.map((h, i) => {
    const x = chronological.length > 1 ? (i / (chronological.length - 1)) * svgW : svgW / 2
    const y = svgH - (h.score / maxScore) * svgH
    return `${x},${y}`
  })
  const trendPath = svgPoints.length > 1 ? `M${svgPoints.join(' L')}` : ''

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <StudentNavbar />

      <main className="flex-1 max-w-[1440px] mx-auto w-full px-8 py-10">
        {/* Header */}
        <section className="mb-10 animate-fade-in">
          <h1 className="text-4xl font-bold text-frost tracking-tight mb-2">My Progress</h1>
          <p className="text-frost-muted text-base">Track your academic growth over time</p>
        </section>

        {hasData ? (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Performance Trend Chart */}
            <div className="md:col-span-8 bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 overflow-hidden">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-frost">Performance Trend</h3>
                  <p className="text-xs text-frost-muted mt-1">Last {data.score_history.length} submissions</p>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${trendBadgeBg(data.improvement.trend)}`}>
                  <div className={`w-2 h-2 rounded-full ${data.improvement.trend === 'improving' ? 'bg-emerald-trust' : data.improvement.trend === 'declining' ? 'bg-coral' : 'bg-frost-muted'} animate-pulse`} />
                  <span>{data.improvement.trend === 'no data' ? 'New' : data.improvement.trend.charAt(0).toUpperCase() + data.improvement.trend.slice(1)}</span>
                </div>
              </div>

              <div className="h-56 w-full flex items-end justify-between gap-1 relative">
                {/* SVG trend line */}
                {trendPath && (
                  <svg className="absolute inset-0 w-full h-full opacity-40" preserveAspectRatio="none" viewBox={`0 0 ${svgW} ${svgH}`}>
                    <defs>
                      <linearGradient id="prog-grad" x1="0%" x2="100%" y1="0%" y2="0%">
                        <stop offset="0%" style={{ stopColor: '#8083ff', stopOpacity: 0.2 }} />
                        <stop offset="100%" style={{ stopColor: '#c0c1ff', stopOpacity: 1 }} />
                      </linearGradient>
                    </defs>
                    <path d={trendPath} fill="none" stroke="url(#prog-grad)" strokeWidth="3" />
                  </svg>
                )}

                {/* Bars */}
                <div className="w-full h-full flex items-end justify-between px-1 relative z-10 gap-1">
                  {barData.map((bar, i) => {
                    const isRecent = i >= barData.length - 3
                    const isLast = i === barData.length - 1
                    return (
                      <div key={i} className="relative flex-1 flex flex-col items-center group">
                        <div
                          className={`w-full max-w-[32px] rounded-t transition-all duration-500 mx-auto ${
                            isRecent ? 'bg-violet-primary/60 shadow-[0_0_10px_rgba(192,193,255,0.3)]' : 'bg-surface-container-highest/80'
                          }`}
                          style={{ height: bar.height }}
                        >
                          {isLast && (
                            <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-violet-primary text-obsidian text-[10px] font-bold px-2 py-0.5 rounded font-mono whitespace-nowrap">
                              {bar.score.toFixed(0)}%
                            </div>
                          )}
                          {/* Tooltip on hover */}
                          <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-surface-container-highest text-frost text-[10px] px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none font-mono z-20">
                            {bar.score.toFixed(1)}% · {bar.topic}
                          </div>
                        </div>
                        {(i % 3 === 0 || isLast) && (
                          <span className="text-[8px] text-frost-muted mt-1 whitespace-nowrap">{bar.label}</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Summary Card */}
            <div className="md:col-span-4 space-y-6">
              {/* Grade */}
              <div className="bg-gradient-to-br from-violet-container/80 to-primary-dim/80 rounded-xl p-6 relative overflow-hidden shadow-lg">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                  <span className="material-symbols-outlined text-7xl">school</span>
                </div>
                <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-2">Cumulative Grade</p>
                <div className="text-5xl font-bold text-white mb-1">{data.summary.cumulative_grade}</div>
                <p className="text-lg text-white/70">GPA: {data.summary.gpa.toFixed(2)}</p>
              </div>

              {/* Score Range */}
              <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-frost-muted mb-4">Score Range</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] text-frost-muted mb-1">Best</p>
                    <span className="text-2xl font-bold font-mono text-emerald-trust">{data.summary.best_score.toFixed(0)}</span>
                  </div>
                  <div>
                    <p className="text-[10px] text-frost-muted mb-1">Worst</p>
                    <span className="text-2xl font-bold font-mono text-coral">{data.summary.worst_score.toFixed(0)}</span>
                  </div>
                  <div>
                    <p className="text-[10px] text-frost-muted mb-1">Average</p>
                    <span className="text-2xl font-bold font-mono text-violet-primary">{data.summary.average_score.toFixed(1)}</span>
                  </div>
                  <div>
                    <p className="text-[10px] text-frost-muted mb-1">Percentile</p>
                    <span className="text-2xl font-bold font-mono text-frost">{data.class_rank.percentile}th</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Full Skill Breakdown */}
            <div className="md:col-span-12 bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-frost">Skill Development</h3>
                <p className="text-xs text-frost-muted mt-1">Your performance across {data.skill_breakdown.length} topic areas</p>
              </div>
              {data.skill_breakdown.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {data.skill_breakdown.map((skill, i) => (
                    <div key={skill.topic_tag} className="bg-surface-container/50 rounded-lg border border-outline-variant/5 p-4">
                      <div className="flex justify-between mb-3">
                        <span className="text-sm font-medium text-frost">{skill.topic_tag}</span>
                        <span className="text-sm font-mono text-violet-primary font-medium">{skill.avg_score.toFixed(1)}%</span>
                      </div>
                      <div className="w-full h-3 bg-surface-container-highest rounded-full overflow-hidden">
                        <div
                          style={{ width: `${Math.min(100, skill.avg_score)}%` }}
                          className={`h-full ${SKILL_COLORS[i % SKILL_COLORS.length]} rounded-full transition-all duration-700`}
                        />
                      </div>
                      <p className="text-[10px] text-frost-muted mt-2">{skill.submission_count} submission{skill.submission_count > 1 ? 's' : ''}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-frost-muted italic">No skill data available yet.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-24 animate-fade-in">
            <div className="w-20 h-20 bg-surface-container-low rounded-2xl mx-auto flex items-center justify-center mb-6 border border-outline-variant/10">
              <span className="material-symbols-outlined text-4xl text-frost-muted">insights</span>
            </div>
            <h2 className="text-xl font-semibold text-frost mb-2">No Progress Data Yet</h2>
            <p className="text-frost-muted max-w-md mx-auto">Submit assignments to start tracking your academic progress.</p>
          </div>
        )}
      </main>

      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
    </div>
  )
}
