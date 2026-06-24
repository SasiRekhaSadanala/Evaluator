'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import AppNavbar from '@/components/AppNavbar'
import { API_BASE } from '@/lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ScoreRecord {
  assignment_id: string
  topic_tag: string
  score: number
  submitted_at: string
}

interface SkillEntry {
  topic_tag: string
  avg_score: number
  submission_count: number
}

interface Achievement {
  icon: string
  title: string
  description: string
  color: string
}

interface StudentProfile {
  student_id: string
  score_history: ScoreRecord[]
  improvement: { delta: number | null; trend: string; prev_avg: number | null }
  class_rank: { percentile: number; class_size: number; student_avg: number | null }
  skill_breakdown: SkillEntry[]
  summary: {
    total_submissions: number
    average_score: number
    best_score: number
    worst_score: number
    cumulative_grade: string
    gpa: number
  }
  achievements: Achievement[]
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

const SKILL_COLORS = [
  'bg-violet-primary',
  'bg-emerald-trust',
  'bg-violet-container',
  'bg-cyan-400',
  'bg-amber-400',
  'bg-rose-400',
  'bg-indigo-400',
]

const ACHIEVEMENT_BG: Record<string, string> = {
  amber: 'from-amber-400 to-amber-500',
  violet: 'from-violet-primary to-violet-container',
  emerald: 'from-emerald-500 to-emerald-600',
  blue: 'from-blue-400 to-blue-500',
}

function trendIcon(trend: string) {
  if (trend === 'improving') return 'trending_up'
  if (trend === 'declining') return 'trending_down'
  return 'trending_flat'
}

function trendBadgeBg(trend: string) {
  if (trend === 'improving') return 'bg-emerald-trust/10 border-emerald-trust/20 text-emerald-trust'
  if (trend === 'declining') return 'bg-coral/10 border-coral/20 text-coral'
  return 'bg-frost-muted/10 border-frost-muted/20 text-frost-muted'
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function StudentProfilePage() {
  const { id } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [profile, setProfile] = useState<StudentProfile | null>(null)

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/students/${id}/profile`)
        if (res.ok) {
          const data = await res.json()
          if (data.status === 'success') {
            setProfile(data)
          } else {
            setError(true)
          }
        } else {
          setError(true)
        }
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [id])

  const displayId = typeof id === 'string' ? id : id?.[0] || 'unknown'

  /* ---- Loading ---- */
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-violet-primary/30 border-t-violet-primary rounded-full animate-spin" />
          <p className="text-sm text-frost-muted">Loading student data...</p>
        </div>
      </div>
    )
  }

  /* ---- Empty / Error state ---- */
  if (error || !profile || profile.summary.total_submissions === 0) {
    return (
      <div className="min-h-screen bg-background text-frost flex flex-col">
        <AppNavbar />
        <main className="flex-1 max-w-[1440px] mx-auto w-full px-8 py-10">
          <Link href="/results" className="inline-flex items-center gap-1 text-sm text-frost-muted hover:text-violet-primary transition-colors mb-6">
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            Back to Results
          </Link>

          <div className="text-center py-24 animate-fade-in">
            <div className="w-20 h-20 bg-surface-container-low rounded-2xl mx-auto flex items-center justify-center mb-6 border border-outline-variant/10">
              <span className="material-symbols-outlined text-4xl text-frost-muted">person_off</span>
            </div>
            <h2 className="text-xl font-semibold text-frost mb-2">No Data Available</h2>
            <p className="text-frost-muted mb-6 max-w-md mx-auto">
              {error
                ? 'Could not connect to the server. Please make sure the backend is running.'
                : `Student "${displayId}" has no submission history yet. Submit assignments to see performance data here.`}
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-primary to-violet-container text-obsidian font-semibold rounded-lg hover:opacity-90 transition-all shadow-violet"
            >
              <span className="material-symbols-outlined text-[18px]">upload</span>
              Upload Submissions
            </Link>
          </div>
        </main>
        <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
          style={{ backgroundImage: `radial-gradient(#c0c1ff 1px, transparent 1px)`, backgroundSize: '32px 32px' }} />
      </div>
    )
  }

  /* ---- Derived data ---- */
  const { score_history, improvement, class_rank, skill_breakdown, summary, achievements } = profile

  // Performance trend bars from real history (chronological: oldest → newest)
  const chronological = [...score_history].reverse()
  const maxScore = 10
  const barData = chronological.map(h => {
    const s10 = h.score <= 10 ? h.score : h.score / 10
    return {
      height: `${Math.max(5, (s10 / maxScore) * 100)}%`,
      score: s10,
      label: formatDate(h.submitted_at),
    }
  })

  // SVG path for the trend line
  const svgWidth = 1000
  const svgHeight = 200
  const svgPoints = chronological.map((h, i) => {
    const s10 = h.score <= 10 ? h.score : h.score / 10
    const x = chronological.length > 1 ? (i / (chronological.length - 1)) * svgWidth : svgWidth / 2
    const y = svgHeight - (s10 / maxScore) * svgHeight
    return `${x},${y}`
  })
  const trendPath = svgPoints.length > 1 ? `M${svgPoints.join(' L')}` : ''

  // Percentile delta text
  const percentileDelta = improvement.delta !== null
    ? `${improvement.delta >= 0 ? '+' : ''}${improvement.delta.toFixed(1)} since last evaluation`
    : 'First evaluation'

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-[1440px] mx-auto w-full px-8 py-10">
        {/* Back link */}
        <Link href="/results" className="inline-flex items-center gap-1 text-sm text-frost-muted hover:text-violet-primary transition-colors mb-6">
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to Results
        </Link>

        {/* Header */}
        <section className="mb-10">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
              <span className="text-xs font-medium text-violet-primary mb-1 block">{displayId}</span>
              <h1 className="text-4xl font-bold text-frost tracking-tight mb-2">
                Student Performance
              </h1>
              <p className="text-frost-muted text-base">
                {summary.total_submissions} submissions · Average {(summary.average_score <= 10 ? summary.average_score : summary.average_score / 10).toFixed(1)}/10 · Grade {summary.cumulative_grade}
              </p>
            </div>
            <div className="flex gap-3">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${trendBadgeBg(improvement.trend)}`}>
                <span className="material-symbols-outlined text-[16px]">{trendIcon(improvement.trend)}</span>
                {improvement.trend === 'no data' ? 'New Student' : improvement.trend.charAt(0).toUpperCase() + improvement.trend.slice(1)}
              </div>
            </div>
          </div>
        </section>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

          {/* ============ Performance Trend Chart ============ */}
          <div className="md:col-span-8 bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 overflow-hidden">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-lg font-semibold text-frost">Performance Trend</h3>
                <p className="text-xs text-frost-muted mt-1">Last {score_history.length} submissions</p>
              </div>
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${trendBadgeBg(improvement.trend)}`}>
                <div className={`w-2 h-2 rounded-full ${improvement.trend === 'improving' ? 'bg-emerald-trust' : improvement.trend === 'declining' ? 'bg-coral' : 'bg-frost-muted'} animate-pulse`} />
                <span>{improvement.trend === 'no data' ? 'New' : improvement.trend.charAt(0).toUpperCase() + improvement.trend.slice(1)}</span>
              </div>
            </div>

            <div className="h-56 w-full flex items-end justify-between gap-1 relative">
              {/* SVG trend line */}
              {trendPath && (
                <svg className="absolute inset-0 w-full h-full opacity-40" preserveAspectRatio="none" viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
                  <defs>
                    <linearGradient id="line-grad" x1="0%" x2="100%" y1="0%" y2="0%">
                      <stop offset="0%" style={{ stopColor: '#8083ff', stopOpacity: 0.2 }} />
                      <stop offset="100%" style={{ stopColor: '#c0c1ff', stopOpacity: 1 }} />
                    </linearGradient>
                  </defs>
                  <path d={trendPath} fill="none" stroke="url(#line-grad)" strokeWidth="3" />
                </svg>
              )}

              {/* Bars */}
              <div className="w-full h-full flex items-end justify-between px-1 relative z-10 gap-1">
                {barData.map((bar, i) => {
                  const isRecent = i >= barData.length - 3
                  const isLast = i === barData.length - 1
                  return (
                    <div key={i} className="relative flex-1 flex flex-col items-center">
                      <div
                        className={`w-full max-w-[32px] rounded-t transition-all duration-500 mx-auto ${isRecent
                            ? 'bg-violet-primary/60 shadow-[0_0_10px_rgba(192,193,255,0.3)]'
                            : 'bg-surface-container-highest/80'
                          }`}
                        style={{ height: bar.height }}
                      >
                        {isLast && (
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-violet-primary text-obsidian text-[10px] font-bold px-2 py-0.5 rounded font-mono whitespace-nowrap">
                            {bar.score.toFixed(1)}/10
                          </div>
                        )}
                      </div>
                      {/* Date label for every 3rd bar */}
                      {(i % 3 === 0 || isLast) && (
                        <span className="text-[8px] text-frost-muted mt-1 whitespace-nowrap">{bar.label}</span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* ============ Class Rank Card ============ */}
          <div className="md:col-span-4 bg-gradient-to-br from-violet-container to-primary-dim rounded-xl p-6 flex flex-col justify-between relative overflow-hidden shadow-lg">
            <div className="absolute top-0 right-0 p-3 opacity-10">
              <span className="material-symbols-outlined text-8xl">workspace_premium</span>
            </div>
            <div className="relative z-10">
              <h3 className="text-lg font-semibold text-white/90">Class Rank</h3>
              <p className="text-xs text-white/60 mt-1">Overall percentile · {class_rank.class_size} students</p>
            </div>
            <div className="relative z-10 py-6">
              <div className="text-6xl font-bold tracking-tight text-white">
                {class_rank.percentile}<span className="text-3xl">th</span>
              </div>
              <p className="text-lg font-medium text-white/80">Percentile</p>
            </div>
            <div className="relative z-10 flex items-center gap-2">
              <span className={`material-symbols-outlined text-white/80 text-[18px]`}>{trendIcon(improvement.trend)}</span>
              <span className="text-xs text-white/70 font-medium">{percentileDelta}</span>
            </div>
          </div>

          {/* ============ Skill Breakdown ============ */}
          <div className="md:col-span-6 bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-frost">Skill Breakdown</h3>
              <p className="text-xs text-frost-muted mt-1">Competency across {skill_breakdown.length} topic areas</p>
            </div>
            {skill_breakdown.length > 0 ? (
              <div className="space-y-5">
                {skill_breakdown.map((skill, i) => (
                  <div className="group" key={skill.topic_tag}>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-frost">{skill.topic_tag}</span>
                      <span className="text-sm font-mono text-violet-primary font-medium">{(skill.avg_score <= 10 ? skill.avg_score : skill.avg_score / 10).toFixed(1)}/10</span>
                    </div>
                    <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
                      <div
                        style={{ width: `${Math.min(100, (skill.avg_score <= 10 ? skill.avg_score * 10 : skill.avg_score))}%` }}
                        className={`h-full ${SKILL_COLORS[i % SKILL_COLORS.length]} rounded-full transition-all duration-500 group-hover:brightness-110`}
                      />
                    </div>
                    <p className="text-[10px] text-frost-muted mt-1">{skill.submission_count} submission{skill.submission_count > 1 ? 's' : ''}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-frost-muted italic">No topic-specific data available yet.</p>
            )}
          </div>

          {/* ============ Academic Summary ============ */}
          <div className="md:col-span-6 bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden flex flex-col">
            <div className="p-6 border-b border-outline-variant/10 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold text-frost">Academic Summary</h3>
                <p className="text-xs text-frost-muted mt-1">ID: {displayId}</p>
              </div>
              <button className="flex items-center gap-2 bg-surface-container-high hover:bg-surface-container-highest text-frost px-4 py-2 border border-outline-variant/10 rounded-lg transition-all text-xs font-medium">
                <span className="material-symbols-outlined text-[16px]">download</span>
                Export
              </button>
            </div>
            <div className="p-6 flex-grow grid grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-frost-muted mb-1">Cumulative Grade</p>
                <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-primary to-violet-container">{summary.cumulative_grade}</div>
              </div>
              <div>
                <p className="text-xs text-frost-muted mb-1">GPA Equivalent</p>
                <div className="text-5xl font-bold text-frost">{summary.gpa.toFixed(2)}</div>
              </div>
              <div>
                <p className="text-xs text-frost-muted mb-1">Best Score</p>
                <div className="text-2xl font-bold font-mono text-emerald-trust">{(summary.best_score <= 10 ? summary.best_score : summary.best_score / 10).toFixed(1)}/10</div>
              </div>
              <div>
                <p className="text-xs text-frost-muted mb-1">Score Range</p>
                <div className="text-2xl font-bold font-mono text-frost">{(summary.worst_score <= 10 ? summary.worst_score : summary.worst_score / 10).toFixed(1)}–{(summary.best_score <= 10 ? summary.best_score : summary.best_score / 10).toFixed(1)}</div>
              </div>

              {/* Achievement badges */}
              {achievements.length > 0 && achievements.map((a, i) => (
                <div key={i} className="col-span-2 p-5 bg-surface-container-lowest border border-outline-variant/10 rounded-xl flex items-center gap-5">
                  <div className={`w-14 h-14 bg-gradient-to-tr ${ACHIEVEMENT_BG[a.color] || ACHIEVEMENT_BG.violet} rounded-full flex items-center justify-center shrink-0 shadow-lg`}>
                    <span className="material-symbols-outlined text-obsidian text-2xl">{a.icon}</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-frost">{a.title}</h4>
                    <p className="text-sm text-frost-muted">{a.description}</p>
                  </div>
                </div>
              ))}

              {achievements.length === 0 && (
                <div className="col-span-2 p-5 bg-surface-container-lowest border border-outline-variant/10 rounded-xl flex items-center gap-5">
                  <div className="w-14 h-14 bg-surface-container-high rounded-full flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-frost-muted text-2xl">emoji_events</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-frost">Keep Going!</h4>
                    <p className="text-sm text-frost-muted">Submit more assignments to earn achievement badges.</p>
                  </div>
                </div>
              )}
            </div>
            <div className="px-6 py-3 bg-surface-container-highest/30 text-[10px] text-frost-muted flex justify-between">
              <span>Generated: {new Date().toISOString().split('T')[0]}</span>
              <span>Evaluator 2.0</span>
            </div>
          </div>

          {/* ============ Submission History Table ============ */}
          <div className="md:col-span-12 bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
            <div className="p-6 border-b border-outline-variant/10">
              <h3 className="text-lg font-semibold text-frost">Submission History</h3>
              <p className="text-xs text-frost-muted mt-1">All {score_history.length} recorded submissions</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-outline-variant/10 text-frost-muted text-xs">
                    <th className="text-left py-3 px-6 font-semibold uppercase tracking-wider">#</th>
                    <th className="text-left py-3 px-6 font-semibold uppercase tracking-wider">Assignment</th>
                    <th className="text-left py-3 px-6 font-semibold uppercase tracking-wider">Topic</th>
                    <th className="text-right py-3 px-6 font-semibold uppercase tracking-wider">Score</th>
                    <th className="text-right py-3 px-6 font-semibold uppercase tracking-wider">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {score_history.map((record, i) => {
                    const s10 = record.score <= 10 ? record.score : record.score / 10
                    const scoreColor =
                      s10 >= 9 ? 'text-emerald-trust' :
                        s10 >= 7 ? 'text-violet-primary' :
                          s10 >= 5 ? 'text-yellow-400' : 'text-coral'
                    return (
                      <tr key={i} className="border-b border-outline-variant/5 hover:bg-surface-container-highest/30 transition-colors">
                        <td className="py-3 px-6 font-mono text-frost-muted text-xs">{String(i + 1).padStart(2, '0')}</td>
                        <td className="py-3 px-6 font-medium text-frost">{record.assignment_id.replace(/_/g, ' ')}</td>
                        <td className="py-3 px-6">
                          <span className="px-2 py-0.5 bg-violet-primary/10 text-violet-primary text-[10px] font-medium rounded-full border border-violet-primary/20">
                            {record.topic_tag || 'General'}
                          </span>
                        </td>
                        <td className={`py-3 px-6 text-right font-mono font-bold ${scoreColor}`}>{s10.toFixed(1)}/10</td>
                        <td className="py-3 px-6 text-right text-frost-muted text-xs">{formatDate(record.submitted_at)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </main>

      {/* Subtle background pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: `radial-gradient(#c0c1ff 1px, transparent 1px)`, backgroundSize: '32px 32px' }} />
    </div>
  )
}
