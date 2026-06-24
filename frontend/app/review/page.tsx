'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import AppNavbar from '@/components/AppNavbar'
import { ResultsStore } from '@/lib/results-store'
import type { EvaluationResult } from '@/lib/results-store'
import { API_BASE } from '@/lib/api'

interface ReviewItem {
  id: string
  submission_id: string
  student_id: string
  assignment_id: string
  trigger: string
  auto_score: number
  flag_reasons: string[]
  status: string
  teacher_score: number | null
  teacher_notes: string | null
  created_at: string
  feedback?: string[]
}

const TRIGGER_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  BOUNDARY:  { label: 'Grade Boundary', color: 'text-amber-400 bg-amber-400/10 border-amber-400/20', icon: 'warning' },
  FLAG:      { label: 'Integrity Flag', color: 'text-coral bg-coral/10 border-coral/20', icon: 'shield' },
  UNCERTAIN: { label: 'AI Uncertain', color: 'text-violet-primary bg-violet-primary/10 border-violet-primary/20', icon: 'help' },
  LOW_SCORE: { label: 'Low Score Alert', color: 'text-red-400 bg-red-400/10 border-red-400/20', icon: 'error' },
  SESSION:   { label: 'Needs Review', color: 'text-amber-400 bg-amber-400/10 border-amber-400/20', icon: 'rate_review' },
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

/**
 * Build review items from session-stored evaluation results.
 * This ensures the review page always has content even when backend
 * DB is unavailable.
 */
function buildSessionReviews(results: EvaluationResult[]): ReviewItem[] {
  return results.map((r, idx) => ({
    id: `session-${idx}`,
    submission_id: r.submission_id,
    student_id: r.submission_id,
    assignment_id: r.batch_id || 'current',
    trigger: r.flag_reasons && r.flag_reasons.length > 0 ? 'FLAG'
      : r.percentage < 30 ? 'LOW_SCORE'
      : 'SESSION',
    auto_score: r.percentage,
    flag_reasons: r.flag_reasons || [],
    status: 'pending',
    teacher_score: null,
    teacher_notes: null,
    created_at: r.evaluated_at || new Date().toISOString(),
    feedback: r.feedback,
  }))
}

export default function ReviewQueuePage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [selectedReview, setSelectedReview] = useState<ReviewItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [overrideScore, setOverrideScore] = useState<number>(0)
  const [teacherNotes, setTeacherNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [dataSource, setDataSource] = useState<'api' | 'session'>('api')

  const fetchReviews = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/reviews?status=pending`)
      if (res.ok) {
        const data = await res.json()
        const items: ReviewItem[] = data.reviews || []
        if (items.length > 0) {
          setReviews(items)
          setSelectedReview(items[0])
          setOverrideScore(Math.round(items[0].auto_score || 0))
          setDataSource('api')
          setLoading(false)
          return
        }
      }
    } catch {
      // Backend may not be running
    }

    // Fallback: Build reviews from session-stored evaluation results
    try {
      const sessionData = ResultsStore.getResults()
      if (sessionData?.status === 'success' && sessionData.results && sessionData.results.length > 0) {
        const sessionReviews = buildSessionReviews(sessionData.results)
        setReviews(sessionReviews)
        setSelectedReview(sessionReviews[0])
        setOverrideScore(Math.round(sessionReviews[0].auto_score || 0))
        setDataSource('session')
      }
    } catch {
      // No session data either
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchReviews()
  }, [])

  const handleOverride = async () => {
    if (!selectedReview) return
    setIsSubmitting(true)
    setSubmitSuccess(false)

    let apiSuccess = false

    // If this is from the API review queue, POST the override
    if (dataSource === 'api' && !selectedReview.id.startsWith('session-')) {
      try {
        const res = await fetch(`${API_BASE}/api/reviews/${selectedReview.id}/override`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ teacher_score: overrideScore, teacher_notes: teacherNotes || 'Manual review completed' })
        })
        if (res.ok) apiSuccess = true
      } catch {
        // Will try direct override below
      }
    }

    // For session-based reviews (or if API review failed), use direct score override
    if (!apiSuccess) {
      try {
        const res = await fetch(`${API_BASE}/api/evaluations/score-override`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: selectedReview.student_id,
            new_score: overrideScore,
            teacher_notes: teacherNotes || 'Manual review completed'
          })
        })
        if (res.ok) apiSuccess = true
      } catch {
        // Backend may not be available
      }
    }

    // Also update session storage so results page reflects the change
    if (apiSuccess) {
      try {
        const sessionData = ResultsStore.getResults()
        if (sessionData?.results) {
          const updated = sessionData.results.map(r =>
            r.submission_id === selectedReview.student_id
              ? { ...r, final_score: overrideScore, percentage: overrideScore }
              : r
          )
          ResultsStore.setResults({ ...sessionData, results: updated })
        }
      } catch {
        // Non-critical
      }
    }

    setSubmitSuccess(true)
    setTimeout(() => {
      const remaining = reviews.filter(r => r.id !== selectedReview.id)
      setReviews(remaining)
      setSelectedReview(remaining[0] || null)
      setTeacherNotes('')
      setSubmitSuccess(false)
      if (remaining[0]) {
        setOverrideScore(Math.round(remaining[0].auto_score || 0))
      }
    }, 800)

    setIsSubmitting(false)
  }

  const selectReview = (review: ReviewItem) => {
    setSelectedReview(review)
    setOverrideScore(Math.round(review.auto_score || 0))
    setTeacherNotes('')
    setSubmitSuccess(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-violet-primary/30 border-t-violet-primary rounded-full animate-spin" />
          <p className="text-sm text-frost-muted">Loading review queue...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <AppNavbar />

      {reviews.length === 0 ? (
        /* Empty State */
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-6 animate-fade-in">
            <div className="w-20 h-20 bg-emerald-trust/10 rounded-2xl mx-auto flex items-center justify-center border border-emerald-trust/20">
              <span className="material-symbols-outlined text-4xl text-emerald-trust">verified_user</span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-frost mb-2">All Clear</h2>
              <p className="text-frost-muted max-w-md">
                No pending reviews. Submit some evaluations first, then flagged submissions will appear here.
              </p>
            </div>
            <div className="flex gap-3 justify-center">
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-primary to-violet-container text-obsidian font-semibold rounded-lg hover:opacity-90 transition-all shadow-violet"
              >
                Upload Submissions
              </Link>
              <Link
                href="/results"
                className="inline-flex items-center gap-2 px-6 py-3 bg-surface-container-high border border-outline-variant/20 text-frost font-medium rounded-lg hover:bg-surface-container-highest transition-all"
              >
                Go to Results
              </Link>
            </div>
          </div>
        </div>
      ) : (
        /* Split Layout */
        <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>
          {/* Left Panel: Review List */}
          <aside className="w-[380px] border-r border-outline-variant/10 bg-surface-container-low overflow-y-auto scrollbar-thin flex-shrink-0">
            <div className="p-5 border-b border-outline-variant/10 flex items-center justify-between sticky top-0 bg-surface-container-low z-10">
              <h3 className="text-sm font-semibold text-frost">
                {dataSource === 'session' ? 'Submissions for Review' : 'Pending Reviews'}
              </h3>
              <span className="px-2 py-0.5 bg-violet-primary/10 text-violet-primary text-xs font-medium rounded-full">
                {reviews.length}
              </span>
            </div>

            {dataSource === 'session' && (
              <div className="px-5 py-2 bg-amber-400/5 border-b border-amber-400/10">
                <p className="text-[10px] text-amber-400 flex items-center gap-1">
                  <span className="material-symbols-outlined text-[14px]">info</span>
                  Showing latest evaluation results for review
                </p>
              </div>
            )}

            <div>
              {reviews.map(review => {
                const triggerInfo = TRIGGER_LABELS[review.trigger] || TRIGGER_LABELS.SESSION
                return (
                  <button
                    key={review.id}
                    onClick={() => selectReview(review)}
                    className={`w-full p-5 text-left transition-all border-b border-outline-variant/5 ${
                      selectedReview?.id === review.id
                        ? 'bg-violet-primary/5 border-l-2 border-l-violet-primary'
                        : 'hover:bg-surface-container-high/30'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-frost truncate mr-2">{review.student_id}</span>
                      <span className={`text-lg font-bold font-mono ${review.auto_score < 50 ? 'text-coral' : review.auto_score >= 90 ? 'text-emerald-trust' : 'text-frost'}`}>
                        {Math.round(review.auto_score)}
                      </span>
                    </div>
                    <p className="text-xs text-frost-muted line-clamp-2 leading-relaxed mb-2">
                      {review.flag_reasons?.length > 0
                        ? review.flag_reasons[0]
                        : `Score ${Math.round(review.auto_score)} — review recommended`}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-medium px-2 py-0.5 rounded border ${triggerInfo.color}`}>
                        {triggerInfo.label}
                      </span>
                      <span className="text-[10px] text-frost-muted">{formatDate(review.created_at)}</span>
                    </div>
                  </button>
                )
              })}
            </div>
          </aside>

          {/* Right Panel: Review Details */}
          <div className="flex-1 bg-background p-8 overflow-y-auto">
            {selectedReview ? (() => {
              const triggerInfo = TRIGGER_LABELS[selectedReview.trigger] || TRIGGER_LABELS.SESSION
              return (
                <div className="max-w-4xl mx-auto space-y-8">
                  {/* Header */}
                  <div>
                    <h1 className="text-2xl font-bold text-frost mb-3">Review Details</h1>
                    <div className="flex items-center gap-3 flex-wrap">
                      <Link
                        href={`/student/${selectedReview.student_id}`}
                        className="text-xs font-medium px-2.5 py-1 rounded-md bg-surface-container-high border border-outline-variant/10 text-violet-primary hover:bg-violet-primary/10 transition-colors"
                      >
                        {selectedReview.student_id}
                      </Link>
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-md border ${triggerInfo.color}`}>
                        <span className="material-symbols-outlined text-[12px] mr-1 align-middle">{triggerInfo.icon}</span>
                        {triggerInfo.label}
                      </span>
                      <span className="text-xs text-frost-muted">{formatDate(selectedReview.created_at)}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Evidence & Reasoning */}
                    <div className="lg:col-span-7 space-y-6">

                      {/* Why this was flagged */}
                      <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
                        <div className="px-5 py-3 border-b border-outline-variant/10 flex items-center gap-2">
                          <span className="material-symbols-outlined text-[16px] text-coral">flag</span>
                          <span className="text-xs font-semibold text-frost-muted uppercase tracking-wider">Why This Was Flagged</span>
                        </div>
                        <div className="p-5 space-y-4">
                          {/* Trigger reason */}
                          <div className="flex items-start gap-3 p-3 bg-surface-container-lowest rounded-lg border border-outline-variant/5">
                            <span className={`material-symbols-outlined text-[20px] mt-0.5 ${
                              selectedReview.trigger === 'FLAG' ? 'text-coral' :
                              selectedReview.trigger === 'UNCERTAIN' ? 'text-violet-primary' : 'text-amber-400'
                            }`}>{triggerInfo.icon}</span>
                            <div>
                              <p className="text-sm font-medium text-frost mb-1">
                                {selectedReview.trigger === 'BOUNDARY' && `Score of ${Math.round(selectedReview.auto_score)} is near a grade boundary (25/50/75)`}
                                {selectedReview.trigger === 'FLAG' && 'Integrity concern detected'}
                                {selectedReview.trigger === 'UNCERTAIN' && 'AI evaluator reported low confidence'}
                                {selectedReview.trigger === 'LOW_SCORE' && `Unusually low score (${Math.round(selectedReview.auto_score)}) — may indicate evaluation issues`}
                                {selectedReview.trigger === 'SESSION' && 'Submission available for manual review'}
                              </p>
                              <p className="text-xs text-frost-muted">
                                {selectedReview.trigger === 'BOUNDARY' && 'Scores within 5 points of a grade boundary are automatically flagged for teacher review to ensure fair grading.'}
                                {selectedReview.trigger === 'FLAG' && 'The integrity system detected potential issues that require human verification.'}
                                {selectedReview.trigger === 'UNCERTAIN' && 'The AI model was not confident in its evaluation. Teacher review ensures accuracy.'}
                                {selectedReview.trigger === 'LOW_SCORE' && 'Very low scores are flagged to ensure the evaluation engine is working correctly.'}
                                {selectedReview.trigger === 'SESSION' && 'Review this submission and adjust the score if needed.'}
                              </p>
                            </div>
                          </div>

                          {/* Flag reasons */}
                          {selectedReview.flag_reasons && selectedReview.flag_reasons.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-frost-muted uppercase tracking-wider mb-2">Integrity Analysis</p>
                              <ul className="space-y-2">
                                {selectedReview.flag_reasons.map((reason, i) => (
                                  <li key={i} className="flex items-start gap-2 text-sm text-frost/80">
                                    <span className="w-1.5 h-1.5 rounded-full bg-coral mt-1.5 shrink-0" />
                                    {reason}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* AI Feedback (from session data) */}
                      {selectedReview.feedback && selectedReview.feedback.length > 0 && (
                        <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
                          <div className="px-5 py-3 border-b border-outline-variant/10 flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px] text-violet-primary">psychology</span>
                            <span className="text-xs font-semibold text-frost-muted uppercase tracking-wider">AI Feedback</span>
                          </div>
                          <div className="p-5 max-h-[300px] overflow-y-auto scrollbar-thin space-y-2">
                            {selectedReview.feedback.map((line, idx) => {
                              if (!line.trim() || line.includes("## AI Evaluator")) return null
                              if (line.startsWith('## ')) {
                                return <h4 key={idx} className="text-sm font-bold text-emerald-trust mt-3 mb-1">{line.replace('## ', '')}</h4>
                              }
                              return <p key={idx} className="text-sm text-frost/80 leading-relaxed">{line}</p>
                            })}
                          </div>
                        </div>
                      )}

                      {/* Submission Info */}
                      <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-5">
                        <div className="flex items-center gap-2 mb-4">
                          <span className="material-symbols-outlined text-[18px] text-emerald-trust">info</span>
                          <span className="text-xs font-semibold uppercase tracking-wider text-frost-muted">Submission Details</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-frost-muted text-xs mb-1">Student ID</p>
                            <p className="font-medium text-frost">{selectedReview.student_id}</p>
                          </div>
                          <div>
                            <p className="text-frost-muted text-xs mb-1">Assignment ID</p>
                            <p className="font-mono text-frost text-xs">{selectedReview.assignment_id}</p>
                          </div>
                          <div>
                            <p className="text-frost-muted text-xs mb-1">AI Score</p>
                            <p className={`font-bold font-mono ${selectedReview.auto_score >= 70 ? 'text-emerald-trust' : selectedReview.auto_score >= 50 ? 'text-amber-400' : 'text-coral'}`}>
                              {selectedReview.auto_score.toFixed(1)}/100
                            </p>
                          </div>
                          <div>
                            <p className="text-frost-muted text-xs mb-1">Submitted</p>
                            <p className="text-frost">{formatDate(selectedReview.created_at)}</p>
                          </div>
                        </div>
                      </div>

                      {/* Link to profile */}
                      <Link
                        href={`/student/${selectedReview.student_id}`}
                        className="flex items-center gap-3 p-4 bg-surface-container-low rounded-xl border border-outline-variant/10 hover:border-violet-primary/30 transition-all group"
                      >
                        <span className="material-symbols-outlined text-violet-primary">person</span>
                        <div>
                          <p className="text-sm font-medium text-frost group-hover:text-violet-primary transition-colors">View Student Profile</p>
                          <p className="text-xs text-frost-muted">See full performance history and trajectory</p>
                        </div>
                        <span className="material-symbols-outlined text-frost-muted ml-auto text-[18px]">chevron_right</span>
                      </Link>
                    </div>

                    {/* Score Override */}
                    <div className="lg:col-span-5">
                      <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 sticky top-8">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-frost-muted mb-6">Manual Score Adjustment</h3>

                        <div className="text-center mb-2">
                          <span className="text-6xl font-bold font-mono text-transparent bg-clip-text bg-gradient-to-r from-violet-primary to-violet-container">
                            {overrideScore}
                          </span>
                          <span className="text-lg text-frost-muted ml-1">/100</span>
                        </div>

                        {/* Show delta from AI score */}
                        <div className="text-center mb-6">
                          {overrideScore !== Math.round(selectedReview.auto_score) ? (
                            <span className={`text-xs font-mono font-medium ${
                              overrideScore > selectedReview.auto_score ? 'text-emerald-trust' : 'text-coral'
                            }`}>
                              {overrideScore > selectedReview.auto_score ? '+' : ''}{overrideScore - Math.round(selectedReview.auto_score)} from AI score
                            </span>
                          ) : (
                            <span className="text-xs text-frost-muted">Same as AI score</span>
                          )}
                        </div>

                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={overrideScore}
                          onChange={(e) => setOverrideScore(parseInt(e.target.value))}
                          className="w-full mb-2"
                        />
                        <div className="flex justify-between text-[10px] text-frost-muted mb-6">
                          <span>0</span>
                          <span>50</span>
                          <span>100</span>
                        </div>

                        <div className="space-y-2 mb-6">
                          <label className="text-xs font-semibold text-frost-muted">Teacher Notes</label>
                          <textarea
                            value={teacherNotes}
                            onChange={(e) => setTeacherNotes(e.target.value)}
                            className="w-full h-[100px] bg-surface-container-lowest border border-outline-variant/20 rounded-lg text-sm p-4 text-frost focus:ring-2 focus:ring-violet-primary/40 focus:border-violet-primary/60 outline-none transition-all placeholder:text-frost-muted/40 resize-none"
                            placeholder="Add justification for this score..."
                          />
                        </div>

                        <button
                          onClick={handleOverride}
                          disabled={isSubmitting}
                          className={`w-full rounded-lg font-semibold text-sm py-3.5 text-obsidian shadow-violet transition-all active:scale-[0.98] disabled:opacity-50 ${
                            submitSuccess
                              ? 'bg-emerald-trust'
                              : 'bg-gradient-to-r from-violet-primary to-violet-container hover:opacity-90'
                          }`}
                        >
                          {submitSuccess ? '✓ Submitted!' : isSubmitting ? 'Submitting...' : 'Submit Override'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })() : (
              <div className="flex items-center justify-center h-full text-frost-muted">
                Select a review from the list
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
