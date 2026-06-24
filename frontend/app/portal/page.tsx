'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import StudentNavbar from '@/components/StudentNavbar'
import { AuthStore } from '@/lib/auth-store'
import { API_BASE } from '@/lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface DashboardData {
  student_id: string
  display_name: string
  summary: {
    total_submissions: number
    average_score: number
    best_score: number
    worst_score: number
    cumulative_grade: string
    gpa: number
  }
  class_rank: { percentile: number; class_size: number; student_avg: number | null }
  improvement: { delta: number | null; trend: string; prev_avg: number | null }
  skill_breakdown: { topic_tag: string; avg_score: number; submission_count: number }[]
  recent_submissions: { assignment_id: string; topic_tag: string; score: number; submitted_at: string }[]
  achievements: { icon: string; title: string; description: string; color: string }[]
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

const SKILL_COLORS = ['bg-violet-primary', 'bg-emerald-trust', 'bg-violet-container', 'bg-cyan-400', 'bg-amber-400', 'bg-rose-400']

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

function trendColor(trend: string) {
  if (trend === 'improving') return 'text-emerald-trust'
  if (trend === 'declining') return 'text-coral'
  return 'text-frost-muted'
}

function scoreColor(score: number) {
  if (score >= 90) return 'text-emerald-trust'
  if (score >= 70) return 'text-violet-primary'
  if (score >= 50) return 'text-yellow-400'
  return 'text-coral'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function StudentDashboard() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<DashboardData | null>(null)

  useEffect(() => {
    const { isAuthenticated, user } = AuthStore.getState()
    if (!isAuthenticated || user?.role !== 'student') {
      router.push('/login')
      return
    }

    const fetchDashboard = async () => {
      try {
        const res = await AuthStore.fetchAuth(`${API_BASE}/api/portal/dashboard`)
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
    fetchDashboard()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-violet-primary/30 border-t-violet-primary rounded-full animate-spin" />
          <p className="text-sm text-frost-muted">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  const hasData = data && data.summary.total_submissions > 0

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <StudentNavbar />

      <main className="flex-1 max-w-[1440px] mx-auto w-full px-8 py-10">
        {/* Welcome Header */}
        <section className="mb-10 animate-fade-in">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
              <h1 className="text-4xl font-bold text-frost tracking-tight mb-2">
                Welcome back, <span className="bg-gradient-to-r from-violet-primary to-violet-container bg-clip-text text-transparent">{data?.display_name?.split(' ')[1] || data?.display_name || 'Student'}</span>
              </h1>
              {hasData ? (
                <p className="text-frost-muted text-base">
                  {data.summary.gpa.toFixed(2)} GPA · {data.class_rank.percentile}th percentile · {data.summary.total_submissions} submission{data.summary.total_submissions !== 1 ? 's' : ''}
                </p>
              ) : (
                <p className="text-frost-muted text-base">Get started by submitting your first assignment</p>
              )}
            </div>
            {hasData && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${
                data.improvement.trend === 'improving' ? 'bg-emerald-trust/10 border-emerald-trust/20 text-emerald-trust'
                : data.improvement.trend === 'declining' ? 'bg-coral/10 border-coral/20 text-coral'
                : 'bg-frost-muted/10 border-frost-muted/20 text-frost-muted'
              }`}>
                <span className="material-symbols-outlined text-[16px]">{trendIcon(data.improvement.trend)}</span>
                {data.improvement.trend === 'no data' ? 'New Student' : data.improvement.trend.charAt(0).toUpperCase() + data.improvement.trend.slice(1)}
              </div>
            )}
          </div>
        </section>

        {hasData ? (
          <>
            {/* Stats Grid */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
              {/* Average Score */}
              <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 hover:border-outline-variant/20 transition-all">
                <p className="text-xs font-semibold uppercase tracking-wider text-frost-muted mb-3">Average Score</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold font-mono text-violet-primary">{data.summary.average_score.toFixed(1)}</span>
                  <span className="text-sm text-frost-muted">/100</span>
                </div>
                <div className="mt-3 h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-violet-primary to-violet-container rounded-full transition-all duration-500" style={{ width: `${data.summary.average_score}%` }} />
                </div>
              </div>

              {/* Class Rank */}
              <div className="bg-gradient-to-br from-violet-container/80 to-primary-dim/80 rounded-xl p-6 relative overflow-hidden shadow-lg">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                  <span className="material-symbols-outlined text-6xl">workspace_premium</span>
                </div>
                <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-3">Class Rank</p>
                <div className="flex items-baseline gap-0.5">
                  <span className="text-3xl font-bold text-white">{data.class_rank.percentile}</span>
                  <span className="text-lg text-white/70">th</span>
                </div>
                <p className="text-xs text-white/50 mt-1">{data.class_rank.class_size} students</p>
              </div>

              {/* Submissions */}
              <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 hover:border-outline-variant/20 transition-all">
                <p className="text-xs font-semibold uppercase tracking-wider text-frost-muted mb-3">Submissions</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold font-mono text-emerald-trust">{data.summary.total_submissions}</span>
                </div>
                <p className="text-xs text-frost-muted mt-1">Grade: {data.summary.cumulative_grade}</p>
              </div>

              {/* Trend */}
              <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 hover:border-outline-variant/20 transition-all">
                <p className="text-xs font-semibold uppercase tracking-wider text-frost-muted mb-3">Trend</p>
                <div className="flex items-center gap-2">
                  <span className={`material-symbols-outlined text-3xl ${trendColor(data.improvement.trend)}`}>
                    {trendIcon(data.improvement.trend)}
                  </span>
                  <div>
                    <p className={`text-sm font-bold ${trendColor(data.improvement.trend)}`}>
                      {data.improvement.delta !== null ? `${data.improvement.delta >= 0 ? '+' : ''}${data.improvement.delta.toFixed(1)}` : '—'}
                    </p>
                    <p className="text-[10px] text-frost-muted">vs recent avg</p>
                  </div>
                </div>
              </div>
            </section>

            {/* Two-Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-10">
              {/* Recent Submissions */}
              <div className="lg:col-span-7 bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
                <div className="p-6 border-b border-outline-variant/10 flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-semibold text-frost">Recent Submissions</h3>
                    <p className="text-xs text-frost-muted mt-1">Your latest evaluations</p>
                  </div>
                  <Link href="/portal/submissions" className="text-xs text-violet-primary hover:text-violet-container transition-colors font-medium">
                    View All →
                  </Link>
                </div>
                <div className="divide-y divide-outline-variant/5">
                  {data.recent_submissions.map((sub, i) => (
                    <div key={i} className="flex items-center justify-between px-6 py-3.5 hover:bg-surface-container-highest/20 transition-colors">
                      <div className="flex items-center gap-3">
                        <span className="text-frost-muted font-mono text-xs w-6">{String(i + 1).padStart(2, '0')}</span>
                        <div>
                          <p className="text-sm font-medium text-frost">{sub.assignment_id.replace(/_/g, ' ')}</p>
                          <span className="px-2 py-0.5 bg-violet-primary/10 text-violet-primary text-[10px] font-medium rounded-full border border-violet-primary/20">
                            {sub.topic_tag || 'General'}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`font-mono font-bold text-sm ${scoreColor(sub.score)}`}>{sub.score.toFixed(1)}</span>
                        <span className="text-[10px] text-frost-muted">{formatDate(sub.submitted_at)}</span>
                      </div>
                    </div>
                  ))}
                  {data.recent_submissions.length === 0 && (
                    <div className="px-6 py-8 text-center text-frost-muted text-sm">No submissions yet</div>
                  )}
                </div>
              </div>

              {/* Skill Breakdown */}
              <div className="lg:col-span-5 bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-frost">Skill Breakdown</h3>
                  <p className="text-xs text-frost-muted mt-1">Competency across {data.skill_breakdown.length} topics</p>
                </div>
                {data.skill_breakdown.length > 0 ? (
                  <div className="space-y-5">
                    {data.skill_breakdown.map((skill, i) => (
                      <div className="group" key={skill.topic_tag}>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm font-medium text-frost">{skill.topic_tag}</span>
                          <span className="text-sm font-mono text-violet-primary font-medium">{(skill.avg_score / 10).toFixed(1)}/10</span>
                        </div>
                        <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <div
                            style={{ width: `${Math.min(100, skill.avg_score)}%` }}
                            className={`h-full ${SKILL_COLORS[i % SKILL_COLORS.length]} rounded-full transition-all duration-500 group-hover:brightness-110`}
                          />
                        </div>
                        <p className="text-[10px] text-frost-muted mt-1">{skill.submission_count} submission{skill.submission_count > 1 ? 's' : ''}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-frost-muted italic">No topic-specific data yet.</p>
                )}
              </div>
            </div>

            {/* Achievements */}
            {data.achievements.length > 0 && (
              <section className="mb-10">
                <h3 className="text-lg font-semibold text-frost mb-4">Achievements</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {data.achievements.map((a, i) => (
                    <div key={i} className="bg-surface-container-low border border-outline-variant/10 rounded-xl p-5 flex items-center gap-4 hover:border-outline-variant/20 transition-all">
                      <div className={`w-12 h-12 bg-gradient-to-tr ${ACHIEVEMENT_BG[a.color] || ACHIEVEMENT_BG.violet} rounded-full flex items-center justify-center shrink-0 shadow-lg`}>
                        <span className="material-symbols-outlined text-obsidian text-xl">{a.icon}</span>
                      </div>
                      <div>
                        <h4 className="font-semibold text-frost text-sm">{a.title}</h4>
                        <p className="text-xs text-frost-muted">{a.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        ) : (
          /* Empty State */
          <div className="text-center py-24 animate-fade-in">
            <div className="w-20 h-20 bg-surface-container-low rounded-2xl mx-auto flex items-center justify-center mb-6 border border-outline-variant/10">
              <span className="material-symbols-outlined text-4xl text-frost-muted">school</span>
            </div>
            <h2 className="text-xl font-semibold text-frost mb-2">No Submissions Yet</h2>
            <p className="text-frost-muted mb-6 max-w-md mx-auto">
              Once your teacher evaluates your assignments, your performance data will appear here.
            </p>
          </div>
        )}
      </main>

      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
    </div>
  )
}
