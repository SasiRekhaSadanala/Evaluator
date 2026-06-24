'use client'

import React, { useState } from 'react'
import Link from 'next/link'

interface ResultCardProps {
  name: string
  percentage: number
  feedback: string[]
  flag_score?: number
  flag_reasons?: string[]
  percentile?: number
  improvement_delta?: number
  trend?: string
  index: number
}

export const ResultCard: React.FC<ResultCardProps> = ({
  name,
  percentage,
  feedback,
  flag_score = 0,
  flag_reasons = [],
  percentile,
  improvement_delta,
  trend,
  index
}) => {
  const [expanded, setExpanded] = useState(false)

  /**
   * Strip Moodle metadata and _Result suffix for display.
   * 'Deeksha Suresh_34567_Result' → 'Deeksha Suresh'
   */
  const cleanDisplayName = (raw: string) => {
    let cleaned = raw.replace(/_Result$/, '')
    cleaned = cleaned.replace(/_\d{4,6}$/, '')
    return cleaned.trim()
  }

  const formatText = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-violet-primary font-semibold">{part.slice(2, -2)}</strong>
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="px-1.5 py-0.5 rounded bg-surface-container-highest text-emerald-trust border border-outline-variant/10 text-[11px] mx-0.5">{part.slice(1, -1)}</code>
      }
      return <span key={i}>{part}</span>
    })
  }

  const hasFlagAlert = flag_score > 0.7 || flag_reasons.length > 0

  const getScoreColor = (score: number) => {
    if (score >= 9) return 'text-emerald-trust'
    if (score >= 7) return 'text-violet-primary'
    if (score >= 5) return 'text-yellow-400'
    return 'text-coral'
  }

  return (
    <div className={`bg-surface-container-low rounded-xl border transition-all duration-300 ${
      expanded
        ? 'border-outline-variant/20 shadow-lg'
        : 'border-outline-variant/10 hover:border-outline-variant/20'
    }`}>
      {/* Header Row */}
      <div
        className="flex items-center justify-between p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-mono text-sm font-bold ${
            percentage >= 90
              ? 'bg-emerald-trust/10 text-emerald-trust'
              : 'bg-surface-container-highest text-frost-muted'
          }`}>
            {index < 10 ? `0${index}` : index}
          </div>
          <div>
            <Link
              href={`/student/${name}`}
              className="text-sm font-semibold text-frost hover:text-violet-primary transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              {cleanDisplayName(name)}
            </Link>
            <p className="text-xs text-frost-muted mt-0.5">
              {trend || 'Evaluation complete'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className={`font-mono text-xl font-bold ${getScoreColor(percentage)}`}>
              {percentage.toFixed(1)}
              <span className="text-xs font-normal text-frost-muted ml-0.5">/10</span>
            </div>
            {(percentile || improvement_delta) && (
              <div className="flex gap-2 text-[10px] text-frost-muted justify-end mt-0.5">
                {percentile ? <span>{percentile}th pctl</span> : null}
                {improvement_delta ? (
                  <span className={improvement_delta >= 0 ? 'text-emerald-trust' : 'text-coral'}>
                    {improvement_delta >= 0 ? '+' : ''}{improvement_delta}%
                  </span>
                ) : null}
              </div>
            )}
          </div>

          {hasFlagAlert && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-coral/10 text-coral rounded-full text-[10px] font-medium border border-coral/20">
              <span className="material-symbols-outlined text-[14px]">warning</span>
              Flagged
            </div>
          )}

          <button
            className="p-1.5 text-frost-muted hover:text-violet-primary transition-colors rounded-md hover:bg-surface-container-high/50"
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          >
            <span className="material-symbols-outlined text-[20px]">
              {expanded ? 'expand_less' : 'expand_more'}
            </span>
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-5 pb-5 border-t border-outline-variant/10 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pt-5">
            {/* AI Feedback */}
            <div className="md:col-span-8 space-y-4">
              <div className="flex items-center gap-2 text-violet-primary">
                <span className="material-symbols-outlined text-[18px]">psychology</span>
                <span className="text-xs font-semibold uppercase tracking-wider">AI Feedback</span>
              </div>

              <div className="bg-surface-container-lowest rounded-lg p-5 max-h-[350px] overflow-y-auto scrollbar-thin space-y-2">
                {feedback && feedback.length > 0 ? (
                  feedback.map((line, idx) => {
                    if (!line.trim() || line.includes("## AI Evaluator")) return null
                    if (line.startsWith('## ')) {
                      return <h4 key={idx} className="text-sm font-bold text-emerald-trust mt-4 mb-2">{line.replace('## ', '')}</h4>
                    }
                    if (line.trim().startsWith('- ')) {
                      return <li key={idx} className="ml-4 list-disc text-sm text-frost/90 leading-relaxed">{formatText(line.replace('- ', ''))}</li>
                    }
                    return <p key={idx} className="text-sm text-frost/80 leading-relaxed">{formatText(line)}</p>
                  })
                ) : (
                  <p className="text-sm text-frost-muted italic">No detailed feedback available.</p>
                )}
              </div>

              {hasFlagAlert && (
                <div className="p-4 rounded-lg border border-coral/20 bg-coral/5">
                  <div className="flex items-center gap-2 text-coral text-xs font-semibold mb-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-coral animate-pulse" />
                    Integrity Concerns
                  </div>
                  <ul className="list-disc ml-5 space-y-1">
                    {flag_reasons.map((r, i) => (
                      <li key={i} className="text-xs text-coral/80">{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="md:col-span-4 flex flex-col justify-center gap-3">
              <Link
                href={`/student/${name}`}
                className="text-center w-full bg-gradient-to-r from-violet-primary to-violet-container text-obsidian text-sm font-semibold py-3 px-6 rounded-lg hover:opacity-90 active:scale-[0.98] transition-all shadow-violet"
              >
                View Student Profile
              </Link>
              <Link
                href="/review"
                className="text-center w-full bg-surface-container-high border border-outline-variant/20 text-frost text-sm font-medium py-3 px-6 rounded-lg hover:bg-surface-container-highest transition-all"
              >
                Manual Review
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
