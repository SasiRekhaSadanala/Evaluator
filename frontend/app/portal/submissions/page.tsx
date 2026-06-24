'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import StudentNavbar from '@/components/StudentNavbar'
import { AuthStore } from '@/lib/auth-store'
import { API_BASE } from '@/lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Submission {
  submission_id: string
  assignment_type: string
  file: string
  final_score: number
  max_score: number
  percentage: number
  feedback: string[]
  integrity_status: string
  evaluated_at: string
  batch_id?: string
  topic_tag?: string
  percentile?: number
  improvement_delta?: number
  trend?: string
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function scoreColor(score: number) {
  if (score >= 90) return 'text-emerald-trust'
  if (score >= 70) return 'text-violet-primary'
  if (score >= 50) return 'text-yellow-400'
  return 'text-coral'
}

function scoreBg(score: number) {
  if (score >= 90) return 'bg-emerald-trust'
  if (score >= 70) return 'bg-violet-primary'
  if (score >= 50) return 'bg-yellow-400'
  return 'bg-coral'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function typeIcon(type: string) {
  if (type === 'code') return 'code'
  if (type === 'content') return 'description'
  return 'assignment'
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function SubmissionsPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  useEffect(() => {
    const { isAuthenticated, user } = AuthStore.getState()
    if (!isAuthenticated || user?.role !== 'student') {
      router.push('/login')
      return
    }

    const fetchSubmissions = async () => {
      try {
        const res = await AuthStore.fetchAuth(`${API_BASE}/api/portal/submissions`)
        if (res.ok) {
          const json = await res.json()
          if (json.status === 'success') setSubmissions(json.submissions || [])
        }
      } catch {
        // Silently handle
      } finally {
        setLoading(false)
      }
    }
    fetchSubmissions()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-violet-primary/30 border-t-violet-primary rounded-full animate-spin" />
          <p className="text-sm text-frost-muted">Loading submissions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <StudentNavbar />

      <main className="flex-1 max-w-[1440px] mx-auto w-full px-8 py-10">
        {/* Header */}
        <section className="mb-10 animate-fade-in">
          <h1 className="text-4xl font-bold text-frost tracking-tight mb-2">My Submissions</h1>
          <p className="text-frost-muted text-base">
            {submissions.length > 0
              ? `${submissions.length} evaluated submission${submissions.length !== 1 ? 's' : ''}`
              : 'View your evaluated assignments and AI feedback'}
          </p>
        </section>

        {submissions.length > 0 ? (
          <div className="space-y-3">
            {submissions.map((sub, idx) => (
              <div key={`${sub.batch_id || idx}-${idx}`} className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden hover:border-outline-variant/20 transition-all">
                {/* Row */}
                <button
                  onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                  className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-surface-container-highest/10 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg ${scoreBg(sub.percentage)}/15 flex items-center justify-center`}>
                      <span className={`material-symbols-outlined text-lg ${scoreColor(sub.percentage)}`}>{typeIcon(sub.assignment_type)}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-frost">
                        {(sub.file || sub.submission_id || 'Submission').replace(/_/g, ' ')}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-0.5 bg-violet-primary/10 text-violet-primary text-[10px] font-medium rounded-full border border-violet-primary/20">
                          {sub.assignment_type || 'unknown'}
                        </span>
                        {sub.topic_tag && (
                          <span className="px-2 py-0.5 bg-surface-container-highest text-frost-muted text-[10px] font-medium rounded-full">
                            {sub.topic_tag}
                          </span>
                        )}
                        {sub.integrity_status === 'under_review' && (
                          <span className="px-2 py-0.5 bg-yellow-500/10 text-yellow-400 text-[10px] font-medium rounded-full border border-yellow-400/20">
                            Under Review
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    {sub.percentile && (
                      <div className="hidden sm:block text-right">
                        <p className="text-[10px] text-frost-muted">Percentile</p>
                        <p className="text-xs font-mono text-frost">{sub.percentile}th</p>
                      </div>
                    )}
                    <div className="text-right">
                      <span className={`text-xl font-bold font-mono ${scoreColor(sub.percentage)}`}>{sub.percentage.toFixed(1)}</span>
                      <span className="text-xs text-frost-muted">/100</span>
                    </div>
                    <div className="text-right hidden sm:block">
                      <p className="text-[10px] text-frost-muted">{sub.evaluated_at ? formatDate(sub.evaluated_at) : '—'}</p>
                    </div>
                    <span className={`material-symbols-outlined text-frost-muted transition-transform duration-200 ${expandedIdx === idx ? 'rotate-180' : ''}`}>
                      expand_more
                    </span>
                  </div>
                </button>

                {/* Expanded Feedback */}
                {expandedIdx === idx && sub.feedback && sub.feedback.length > 0 && (
                  <div className="px-6 pb-5 pt-1 border-t border-outline-variant/10 animate-slide-down">
                    <h4 className="text-xs font-semibold text-frost-muted uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span className="material-symbols-outlined text-[14px]">smart_toy</span>
                      AI Feedback
                    </h4>
                    <div className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin">
                      {sub.feedback.map((line, i) => {
                        const isBold = line.startsWith('**') || line.includes('Summary') || line.includes('Corrections') || line.includes('Strengths')
                        return (
                          <p key={i} className={`text-sm leading-relaxed ${isBold ? 'text-frost font-semibold mt-3' : 'text-frost-muted'}`}>
                            {line}
                          </p>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          /* Empty State */
          <div className="text-center py-24 animate-fade-in">
            <div className="w-20 h-20 bg-surface-container-low rounded-2xl mx-auto flex items-center justify-center mb-6 border border-outline-variant/10">
              <span className="material-symbols-outlined text-4xl text-frost-muted">assignment</span>
            </div>
            <h2 className="text-xl font-semibold text-frost mb-2">No Submissions Yet</h2>
            <p className="text-frost-muted mb-6 max-w-md mx-auto">
              Your evaluated assignments will appear here with detailed AI feedback.
            </p>
          </div>
        )}
      </main>

      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
    </div>
  )
}
